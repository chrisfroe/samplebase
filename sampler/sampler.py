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

    @staticmethod
    def task(params):
        """Wrap the function to be performed to also do the argument-fetching and result-writing

        Fetch the arguments from sample_file, reading in array data from other places if necessary (read only).
        Perform the function func with given arguments.
        Save any array data to new files and save path to results.
        Write results to sample_file.
        """
        func, sample_dir, sample_file_path = params

        # @todo delegate to other static methods
        with open(sample_file_path, "r") as sample_file:
            sample = json.load(sample_file)
        pure_args = Sampler.pure_data(sample, sample_dir, target="args")

        pure_result = func(**pure_args)

        processed_result = Sampler.processed_data(pure_result, sample_dir)
        if "result" in sample:
            sample.pop("result")
        sample["result"] = processed_result
        with open(sample_file_path, "w") as sample_file:
            json.dump(sample, sample_file)

    def sample(self, n_jobs=1):
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
            for _, _ in enumerate(p.imap_unordered(Sampler.task, task_arguments, 1)):
                pass

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
        sample_data = {
            "name": name,
            "done": False,
            "args": Sampler.processed_data(input_args, sample_dir)
        }
        sample_file_path = os.path.join(sample_dir, name + ".json")
        with open(sample_file_path, "w") as outfile:
            json.dump(sample_data, outfile)

    @staticmethod
    def processed_data(pure_data, sample_dir):
        """
        Transform pure_data (key, value) pairs according to specification.
        This involves saving arrays to sample_dir.
        """
        arrays = Sampler.extract_if(pure_data, lambda x: isinstance(x, np.ndarray))
        scalars = Sampler.extract_if(pure_data, lambda x: not hasattr(x, "__len__"))
        strings = Sampler.extract_if(pure_data, lambda x: isinstance(x, str))
        arrays = Sampler.insert_file_layer(arrays, sample_dir)
        scalars = Sampler.insert_value_layer(scalars)
        strings = Sampler.insert_value_layer(strings)
        processed_args = dict()
        processed_args.update(arrays)
        processed_args.update(scalars)
        processed_args.update(strings)
        return processed_args

    @staticmethod
    def pure_data(sample, sample_dir, target="args"):
        """Transform saved data according to specification to pure data again, i.e. (key, value) pairs"""
        args = sample[target]
        _pure_data = dict()
        for key, value in args.items():
            if "value" in value:
                _pure_data[key] = value["value"]
            elif "file" in value:
                # @todo ask for key of npy files
                file_path = os.path.join(sample_dir, value["file"]["path"])
                with np.load(file_path) as file_arr:
                    _pure_data[key] = np.copy(file_arr)
        return _pure_data

    def remove(self, name):
        """Remove sample with name"""
        raise RuntimeError("impl this")

    def remove_if(self, matcher):
        """Remove sample if the matcher evaluates to True. Matcher is function: sample -> bool"""
        raise RuntimeError("impl this")

    def result(self, name):
        """Return the result dict of sample with name"""
        # @todo process results to pure_results that contain loaded arrays as well
        with os.scandir(self._samples_dir) as it:
            for sample in it:
                if sample.is_dir() and sample.name == name:
                    sample_dir = os.path.join(self._samples_dir, name)
                    sample_file_path = os.path.join(sample_dir, name + ".json")
                    with open(sample_file_path, "r") as sample_file:
                        loaded = json.load(sample_file)
                    return Sampler.pure_data(loaded, sample_dir, "result")

    @staticmethod
    def extract_if(input_args=None, func=lambda x: x is None):
        """From dict input_args extract elements, whose values positively evaluate func"""
        if input_args is None:
            input_args = dict()
        extract = dict()
        for key, value in input_args.items():
            if func(value):
                extract[key] = value
        return extract

    @staticmethod
    def insert_value_layer(input_args=None):
        """Transform input_args from {key:value} to {key: {"value": value}} according to specification of a sample"""
        if input_args is None:
            input_args = dict()
        processed = dict()
        for key, value in input_args.items():
            processed[key] = {"value": value}
        return processed

    @staticmethod
    def insert_file_layer(input_args=None, sample_dir=os.getcwd()):
        """Transform input_args from {key:value} to {key: {"file": arr/path/relative/to/sample/dir}}"""
        if input_args is None:
            input_args = dict()
        processed = dict()
        for key, value in input_args.items():
            file_name = key + stamp()
            file_path = os.path.join(sample_dir, "args", file_name)
            np.save(file_path, value)
            processed[key] = {"file": "args/" + file_name}
        return processed
