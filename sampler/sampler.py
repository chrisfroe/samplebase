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


def stamp():
    """
    Generate a string based on the current date, time and an 8-digit
    random string, which shall be guarantee enough not to generate the same string twice

    """
    timestamp = time.strftime("%Y_%m_%d-%H_%M_%S")
    randomstamp = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(8))
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
        samples_dir = os.path.join(prefix, name)
        if os.path.exists(samples_dir):
            log.info("samples_dir exists")
            if resample:
                log.info("results will be computed again")
            else:
                log.info("existing results will be skipped")
        else:
            os.makedirs(samples_dir, exist_ok=False)

    def sample(self):
        """Perform the function for all input_args"""
        # gather tasks
        # perform

    def add_sample(self, input_args):
        """Add a point in argument space to be sampled for results.

        A new entry under 'samples' in json config file is created.
        Scalar input args are directly written into the json config, arrays are written to a file,
        whose path will be saved in the config entry.
        """
        pass
