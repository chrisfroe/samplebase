# coding=utf-8

"""Sample results from an argument space. Handle and provide access to output files"""

import numpy as np
import time
import random
import string
import json
import logging

import sampler.logutil as logutil

__license__ = "LGPL"
__author__ = "chrisfroe"

logging.basicConfig(format='[sampler] [%(asctime)s] [%(levelname)s] %(message)s', level=logging.DEBUG, datefmt="%Y-%m-%d %H:%M:%S")
log = logutil.StyleAdapter(logging.getLogger(__name__))


# generate a string based on the current time and a 6-digit random string
def stamp():
    timestamp = time.strftime("%Y_%m_%d-%H_%M_%S")
    randomstamp = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(6))
    _stamp = timestamp + "_" + randomstamp
    return _stamp


class Sampler:
    def __init__(self, name, prefix, func, n_jobs):
        self.n_jobs = n_jobs
        self._name = name
        self._func = func
        self._prefix = prefix
        self._input_args = []

    def sample(self):
        """Perform the function for all input_args"""
        # gather tasks
        # perform

    def add_sample(self, input_args):
        pass
