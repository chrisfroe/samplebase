# coding=utf-8

"""Sample results from an argument space. Handle and provide access to output files"""

import os
import time
import random
import string
import json
import numpy as np
import logging
import pathos.multiprocessing as pm
import shutil

import sampler.logutil as logutil

__license__ = "LGPL"
__author__ = "chrisfroe"

logging.basicConfig(format='[sampler] [%(asctime)s] [%(levelname)s] %(message)s', level=logging.INFO,
                    datefmt="%Y-%m-%d %H:%M:%S")
log = logutil.StyleAdapter(logging.getLogger(__name__))


def stamp(random_digits=8):
    """
    Generate a string based on the current date, time and an 8-digit
    random string, which shall be guarantee enough not to generate the same string twice
    """
    timestamp = time.strftime("%Y_%m_%d-%H_%M_%S")
    randomstamp = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(random_digits))
    _stamp = timestamp + "_" + randomstamp
    return _stamp


class Sampler:
    """
    Sampler object is rather stateless, the state is given by what samples exist on the filesystem.
    Samples themselves are not held by Sampler, they are fetched lazily, when accessing the data or actually sampling.
    """

    def __init__(self, name, prefix, func, resample=False):
        self._func = func
        self._samples_dir = os.path.join(prefix, name)
        if os.path.exists(self._samples_dir):
            log.info("samples_dir {} exists", self._samples_dir)
            if resample:
                log.info("results will be computed again")
            else:
                log.info("existing results will be skipped")
        else:
            os.makedirs(self._samples_dir, exist_ok=False)

    @property
    def samples_dir(self):
        return self._samples_dir

    @property
    def samples(self):
        # @todo first: greedy gather a new list of Samples
        # @todo second: keep a cached version, check if samples_dir has been touched, if so update list
        return []

    def add(self, input_args, name=stamp()):
        """Add a point in argument space to be sampled for results.

        A new sub_dir in samples_dir is created
        Scalar input args are directly written into the json config, arrays are written to a file,
        whose path will be saved in the config entry.
        """
        # @todo how to serialize objects into these args as well
        sample_dir = os.path.join(self._samples_dir, name)
        os.makedirs(sample_dir, exist_ok=False)
        args_dir = os.path.join(sample_dir, "args")
        os.makedirs(args_dir, exist_ok=False)
        result_dir = os.path.join(sample_dir, "result")
        os.makedirs(result_dir, exist_ok=False)
        sample_data = {
            "name": name,
            "done": False,
            "args": Sampler._processed_data(input_args, sample_dir, file_target="args")
        }
        sample_file_path = os.path.join(sample_dir, name + ".json")
        with open(sample_file_path, "w") as outfile:
            json.dump(sample_data, outfile)

    def remove(self, name):
        """Remove sample with name"""
        with os.scandir(self._samples_dir) as it:
            for sample in it:
                if sample.is_dir() and sample.name == name:
                    sample_dir = os.path.join(self._samples_dir, name)
                    shutil.rmtree(sample_dir)

    def remove_if(self, matcher):
        """Remove sample if the matcher evaluates to True. Matcher is function: sample -> bool"""
        with os.scandir(self._samples_dir) as it:
            for sample in it:
                if sample.is_dir():
                    sample_dir = os.path.join(self._samples_dir, sample.name)
                    sample_file_path = os.path.join(sample_dir, sample.name + ".json")
                    with open(sample_file_path, "r") as sample_file:
                        loaded_sample = json.load(sample_file)
                    _pure_sample = Sampler._pure_sample(loaded_sample, sample_dir)
                    if matcher(_pure_sample):
                        shutil.rmtree(sample_dir)
                        return

    def result(self, name):
        """Return the result dict of sample with name"""
        with os.scandir(self._samples_dir) as it:
            for sample in it:
                if sample.is_dir() and sample.name == name:
                    sample_dir = os.path.join(self._samples_dir, name)
                    sample_file_path = os.path.join(sample_dir, name + ".json")
                    with open(sample_file_path, "r") as sample_file:
                        loaded = json.load(sample_file)
                    return Sampler._pure_data(loaded, sample_dir, "result")

    def run(self, n_jobs=2):
        """Perform the function for all input_args

        Gather tasks, then perform by spawning multiple threads.
        """
        task_arguments = []
        with os.scandir(self._samples_dir) as it:
            for sample in it:
                if sample.is_dir():
                    sample_dir = os.path.join(self._samples_dir, sample.name)
                    sample_file_path = os.path.join(sample_dir, sample.name + ".json")
                    with open(sample_file_path, "r") as sample_file:
                        loaded = json.load(sample_file)
                    if not loaded["done"]:
                        task_arguments.append((self._func, sample_dir, sample_file_path))

        with pm.Pool(processes=n_jobs) as p:
            for _, _ in enumerate(p.imap_unordered(Sampler._task, task_arguments, 1)):
                pass

    @staticmethod
    def _task(params):
        """Wrap the function to be performed to also do the argument-fetching and result-writing

        Fetch the arguments from sample_file, reading in array data from other places if necessary (read only).
        Perform the function func with given arguments.
        Save any array data to new files and save path to results.
        Write results to sample_file.
        """
        func, sample_dir, sample_file_path = params

        with open(sample_file_path, "r") as sample_file:
            sample = json.load(sample_file)
        pure_args = Sampler._pure_data(sample, sample_dir, target="args")

        pure_result = func(**pure_args)

        processed_result = Sampler._processed_data(pure_result, sample_dir, file_target="result")
        if "result" in sample:
            sample.pop("result")
        sample["result"] = processed_result
        with open(sample_file_path, "w") as sample_file:
            json.dump(sample, sample_file)

    @staticmethod
    def _extract_if(data_dict=None, func=lambda x: x is None):
        """From data_dict extract elements, whose values positively evaluate func"""
        if data_dict is None:
            data_dict = dict()
        extract = dict()
        for key, value in data_dict.items():
            if func(value):
                extract[key] = value
        return extract

    @staticmethod
    def _insert_value_layer(data_dict=None):
        """Transform data_dict from {key:value} to {key: {"value": value}} according to specification of a sample"""
        if data_dict is None:
            data_dict = dict()
        processed = dict()
        for key, value in data_dict.items():
            processed[key] = {"value": value}
        return processed

    @staticmethod
    def _insert_file_layer(data_dict=None, sample_dir=os.getcwd(), file_target="args"):
        """Transform data_dict from {key:value} to {key: {"file": arr/path/relative/to/sample/dir}}

        Saves all values to .npy files"""
        if data_dict is None:
            data_dict = dict()
        processed = dict()
        for key, value in data_dict.items():
            file_name = key + stamp() + ".npy"
            file_path = os.path.join(sample_dir, file_target, file_name)
            np.save(file_path, value)
            processed[key] = {"file": file_target + "/" + file_name}
        return processed

    @staticmethod
    def _pure_sample(loaded_sample, sample_dir):
        """Transform saved sample according to specification to pure sample again"""
        _pure_sample = dict()
        _pure_sample["done"] = loaded_sample["done"]
        _pure_sample["name"] = loaded_sample["name"]
        _pure_sample["args"] = Sampler._pure_data(loaded_sample, sample_dir, target="args")
        _pure_sample["result"] = Sampler._pure_data(loaded_sample, sample_dir, target="result")
        return _pure_sample

    @staticmethod
    def _pure_data(sample, sample_dir, target="args"):
        """Transform saved data according to specification to pure data again, i.e. (key, value) pairs"""
        _pure_data = dict()
        if target in sample:
            loaded_data = sample[target]
            for key, value in loaded_data.items():
                if "value" in value:
                    _pure_data[key] = value["value"]
                elif "file" in value:
                    file_path = os.path.join(sample_dir, os.path.normpath(value["file"]))
                    _pure_data[key] = np.load(file_path)
        return _pure_data

    @staticmethod
    def _processed_data(pure_data, sample_dir, file_target="args"):
        """
        Transform pure_data (key, value) pairs according to specification.
        This involves saving arrays to sample_dir.
        """
        arrays = Sampler._extract_if(pure_data, lambda x: isinstance(x, np.ndarray))
        scalars = Sampler._extract_if(pure_data, lambda x: not hasattr(x, "__len__"))
        strings = Sampler._extract_if(pure_data, lambda x: isinstance(x, str))
        arrays = Sampler._insert_file_layer(arrays, sample_dir, file_target)
        scalars = Sampler._insert_value_layer(scalars)
        strings = Sampler._insert_value_layer(strings)
        processed_args = dict()
        processed_args.update(arrays)
        processed_args.update(scalars)
        processed_args.update(strings)
        return processed_args


class CachedArray:
    """Array which resides on disk, and is only loaded when explicitly obtained, i.e. __get__"""
    def __init__(self, file_path):
        self._file_path = file_path
        self._cached_value = None
        self._first_get = True

    def __get__(self, instance, owner):
        if self._first_get:
            self._first_get = False
            self._update_cached_value()
        elif self._changed():
            self._update_cached_value()
        return self._cached_value

    def _changed(self):
        return False

    def _update_cached_value(self):
        self._cached_value = np.load(self._file_path)
        pass


class Sample:
    """Provide read only access to samples on disk. Data is only read from disk if it changed.

    @todo hold a lock on json file or whole sample_dir, that protects against files being moved?
    @todo Cache json file, reload it if it has changed. How to do that?
    """

    def __init__(self, sample_dir, sample_name):
        self.cached_pure_sample = None

    @property
    def args(self):
        """Return copy of args"""
        if self.changed():
            self.update_cache()
        return self.cached_pure_sample["args"]

    @property
    def result(self):
        """Return copy of result"""
        if self.changed():
            self.update_cache()
        return self.cached_pure_sample["args"]

    def changed(self):
        """Check if the json file changed"""
        return False

    def update_cache(self):
        """Read json file, convert to pure, write to cached_pure_sample. The pure cache directly holds
        scalar data. For arrays it holds another cached object, which is only read when needed"""
        pass
