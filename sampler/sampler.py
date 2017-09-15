# coding=utf-8

"""Sample results from an argument space. Handle and provide access to output files"""

import os
import time
import random
import string
import json
import numpy as np
import logging

import sampler.logutil as logutil

__license__ = "LGPL"
__author__ = "chrisfroe"

logging.basicConfig(format='[sampler] [%(asctime)s] [%(levelname)s] %(message)s', level=logging.DEBUG, datefmt="%Y-%m-%d %H:%M:%S")
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
    Sampler object is rather stateless, only needs location to samples_dir. Samples themselves are not held by Sampler,
    they are fetched lazily, when accessing the data or actually sampling.
    """

    def __init__(self, name, prefix, func, n_jobs=2, resample=False):
        self._func = func
        self.n_jobs = n_jobs
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

    def sample(self):
        """Perform the function for all input_args"""
        # gather tasks
        # perform

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
        arrays = self.extract_if(input_args, lambda x: isinstance(x, np.ndarray))
        scalars = self.extract_if(input_args, lambda x: not hasattr(x, "__len__"))
        strings = self.extract_if(input_args, lambda x: isinstance(x, str))
        arrays = self.insert_file_layer(arrays, sample_dir)
        scalars = self.insert_value_layer(scalars)
        strings = self.insert_value_layer(strings)
        processed_args = dict()
        processed_args.update(scalars)
        processed_args.update(strings)

        sample_data = {
            "name": name,
            "done": False,
            "args": processed_args
        }
        config_path = os.path.join(sample_dir, name + ".json")
        with open(config_path, 'w') as outfile:
            json.dump(sample_data, outfile)

    def remove(self, name):
        """Remove sample with name"""
        raise RuntimeError("impl this")

    def remove_if(self, matcher):
        """Remove sample if the matcher evaluates to True. Matcher is function: sample -> bool"""
        raise RuntimeError("impl this")

    def result(self, name):
        """Return the result dict of sample with name"""
        raise RuntimeError("impl this")

    @classmethod
    def extract_if(cls, input_args=None, func=lambda x: x is None):
        """From dict input_args extract elements, whose values positively evaluate func"""
        if input_args is None:
            input_args = dict()
        extract = dict()
        for key, value in input_args.items():
            if func(value):
                extract[key] = value
        return extract

    @classmethod
    def insert_value_layer(cls, input_args=None):
        """Transform input_args from {key:value} to {key: {"value": value}} according to specification of a sample"""
        if input_args is None:
            input_args = dict()
        processed = dict()
        for key, value in input_args.items():
            processed[key] = {"value": value}
        return processed

    @classmethod
    def insert_file_layer(cls, input_args=None, sample_dir=os.getcwd()):
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
