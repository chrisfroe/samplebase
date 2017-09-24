# coding=utf-8

"""Sample results from an argument space. Handle and provide access to output files"""

import os
import time
import random
import string
import json
import jsonpickle
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


# @todo to guarantee safe parallel access, set up a mini server, that holds the list of samples

class Sample(object):
    # assume that the file will only be manipulated by this object, thus no watching required
    def __init__(self, parent_prefix, name=None, args=None):
        if not ((name is not None) or (args is not None)):
            raise RuntimeError("Either name or initial arguments (or both) must be given.")
        if args is None:
            args = dict()
        if name is None:
            name = stamp()
        self._data = None
        self._outdated = True
        self._prefix = os.path.join(parent_prefix, name)
        self._data_path = os.path.join(self._prefix, name + ".json")
        if not os.path.exists(self._prefix):
            os.makedirs(self._prefix, exist_ok=False)

        if not os.path.exists(self._data_path):
            self._data = {
                "name": name,
                "done": False,
                "args": args
            }
            self._write()

    @property
    def name(self):
        return self["name"]

    @property
    def done(self):
        if self._outdated:
            self._read()
        return self["done"]

    @property
    def args(self):
        return self["args"]

    @property
    def result(self):
        if self._outdated:
            self._read()
        if "result" in self._data:
            return self["result"]
        return {}

    @result.setter
    def result(self, value):
        self._data["result"] = value
        self._data["done"] = True
        self._write()

    def __getitem__(self, item):
        if self._outdated:  # currently the only way to outdate the data is by another process
            self._read()
        return self._data[item]

    def _write(self):
        storage_data = Sample._convert_to_storage_data(self._data, self._prefix)
        with open(self._data_path, "w") as outfile:
            json.dump(storage_data, outfile)

    def _read(self):
        with open(self._data_path, "r") as infile:
            storage_data = json.load(infile)
        self._data = Sample._convert_to_pure_data(storage_data, self._prefix)
        self._outdated = False

    @staticmethod
    def _convert_to_storage_data(data, save_prefix):
        storage_data = dict()
        for key, value in data.items():
            if isinstance(value, str):
                storage_data[key] = {"value": value}
            elif isinstance(value, np.ndarray):
                file_name = key + stamp() + ".npy"
                file_path = os.path.join(save_prefix, file_name)
                np.save(file_path, value)
                storage_data[key] = {"ndarray": file_name}
            elif isinstance(value, dict):
                storage_data[key] = {"dict": Sample._convert_to_storage_data(value, save_prefix)}
            elif not hasattr(value, "__len__"):
                storage_data[key] = {"value": value}
            else:
                # lists and unknown objects are json-pickled
                pickled = jsonpickle.encode(value)
                file_name = key + stamp() + ".json"
                file_path = os.path.join(save_prefix, file_name)
                with open(file_path, "w") as out:
                    out.write(pickled)
                storage_data[key] = {"pickled": file_name}
        return storage_data

    @staticmethod
    def _convert_to_pure_data(storage_data, save_prefix):
        pure_data = dict()
        for key, value in storage_data.items():
            if "value" in value:
                pure_data[key] = value["value"]
            elif "ndarray" in value:
                # @todo instead of loadings arrays place CachedArrays at the corresponding locations
                file_name = value["ndarray"]
                file_path = os.path.join(save_prefix, file_name)
                pure_data[key] = np.load(file_path)
            elif "pickled" in value:
                file_name = value["pickled"]
                file_path = os.path.join(save_prefix, file_name)
                with open(file_path, "r") as infile:
                    pickled = infile.read()
                pure_data[key] = jsonpickle.decode(pickled)
            elif "dict" in value:
                pure_data[key] = Sample._convert_to_pure_data(value["dict"], save_prefix)
            else:
                raise RuntimeError("Unknown storage data object with key " + key)
        return pure_data


def list_of_samples(samples_dir=os.getcwd()):
    samples = []
    with os.scandir(samples_dir) as it:
        for sample in it:
            if sample.is_dir():
                samples.append(Sample(samples_dir, sample.name))
    return samples


def run(func, samples, n_jobs=1):
    """Process samples in parallel"""

    def task(sample):
        sample.result = func(**sample.args)

    todo_samples = [s for s in samples if not s.done]

    with pm.Pool(processes=n_jobs) as p:
        for _, _ in enumerate(p.imap_unordered(task, todo_samples, 1)):
            pass

    for s in todo_samples:
        s._outdated = True
