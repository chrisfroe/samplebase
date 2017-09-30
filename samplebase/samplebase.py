# coding=utf-8

"""Sample results from an argument space. Handle and provide access to output files

In-process (server-less), file-local, ad-hoc, document-based database of samples/tasks
and parallel map() utility to process the samples. Each sample is an independent object handling
its own IO. This allows to trivially parallelise mapping a function onto a list of samples. Safe concurrent
read/write is attempted by file-locking. Integrity of a sample is achieved by allowing only one writing user
at a time, also via file-locking.
"""

import os
import logging
import pathos.multiprocessing as pm

import samplebase.logutil as logutil
from samplebase.sample import *

__license__ = "LGPL"
__author__ = "chrisfroe"

logging.basicConfig(format='[samplebase] [%(asctime)s] [%(levelname)s] %(message)s', level=logging.INFO,
                    datefmt="%Y-%m-%d %H:%M:%S")
log = logutil.StyleAdapter(logging.getLogger(__name__))


def list_of_samples(samples_dir):
    """
    Return read-only samples from given directory. These objects will not reflect future changes
    on disk. For this purpose, acquire a new list of samples.
    """
    samples = []
    with os.scandir(samples_dir) as it:
        for sample in it:
            if sample.is_dir():
                samples.append(Sample(samples_dir, sample.name))
    return samples


def names_of_samples(samples_dir):
    names = []
    with os.scandir(samples_dir) as it:
        for sample in it:
            if sample.is_dir():
                names.append(sample.name)
    return names


def run_parallel(func, prefix, sample_names, n_jobs=1):
    """Map func on args to get results. Only process sample if it is not done."""

    def task(name):
        with SampleContextManager(prefix, name) as sample:
            if not sample.done:
                sample.result = func(**sample.args)

    with pm.Pool(processes=n_jobs) as p:
        for _ in p.imap_unordered(task, sample_names, 1):
            pass


def process_parallel(func, prefix, sample_names, n_jobs=1):
    """Similar to run, but map func on samples, to do whatever. Useful for pre/post processing of args or results"""

    def task(name):
        with SampleContextManager(prefix, name) as sample:
            func(sample)

    with pm.Pool(processes=n_jobs) as p:
        for _ in p.imap_unordered(task, sample_names, 1):
            pass
