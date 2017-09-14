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
        sample_dir = os.path.join(self._samples_dir, name)
        os.makedirs(sample_dir, exist_ok=False)
        args_dir = os.path.join(sample_dir, "args")
        os.makedirs(args_dir, exist_ok=False)
        arrays = self.extract_if(input_args, lambda x: isinstance(x, np.ndarray))
        scalars = self.extract_if(input_args, lambda x: not hasattr(x, "__len__"))
        strings = self.extract_if(input_args, lambda x: isinstance(x, str))
        # @todo process arrays: save them to file and prepare a dict {name: {file: path}, name2: {file: path2}}
        # @todo process strings and scalars: introduce 'value' layer in dict: {name: {value: val}, name2: {value: val2}}
        processed_args = dict()
        processed_args.update(scalars)
        processed_args.update(strings)

        sample_data = {
            "name": name,
            "done": False,
            "args": input_args
        }

    def remove(self, name):
        """Remove sample with name"""
        pass

    def remove_if(self, matcher):
        """Remove sample if the matcher evaluates to True. Matcher is function: sample -> bool"""
        pass

    def result(self, name):
        """Return the result dict of sample with name"""
        pass

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
