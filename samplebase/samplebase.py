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


# @todo to guarantee safe parallel access, set up a mini server, that holds the list of samples
# @todo how to move already existing files into sample_dir, e.g. created during task() or given as args or result
# better: run_task to do pre/post-processing

# @todo time_it decorator for tasks, some log statements

# @todo client server structure:
# - with sockets and the serversocket bound to 'localhost' https://docs.python.org/3.6/howto/sockets.html
#   this would be best if samples should at some point be available remotely
# - named pipes in python are like files, which are written to by one process and read by another
# - message Queue in python to function in a similar way

# server has to know which samples to hold, but this is information that only clients have

# server holds lists of samples, and passes these to clients (only pickled storage_data.json,
# the client will have to load additional files). Sample will then be blocked (for writing!), until
# the client messages that he is done (i.e. client has written additional files and gives back the pickled .json).
# then the sample is unlocked again on the server and free for use.

# clients will use a Sample object with a contextmanager such that aquiring
# message and closing message is done via scope.

# @fixme server/user handles IO in anyway, server could give out ThinSample(prefix, name), so that workers can aquire the actual Sample from server

# @fixme on creation, select mode 'w' or 'r',
# 'w': is used for creating new samples and writing results,
# creates a lock on the sample via file '*.json.lock', with renaming operation, that throws when lock already exists
# i.e. sample is manually locked on creation and should be closed, maybe with context manager (RAII)
# 'r': is only used for reading,


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
        for _, _ in enumerate(p.imap_unordered(task, sample_names, 1)):
            pass


def process_parallel(func, prefix, sample_names, n_jobs=1):
    """Similar to run, but map func on samples, to do whatever. Useful for pre/post processing of args or results"""

    def task(name):
        with SampleContextManager(prefix, name) as sample:
            func(sample)

    with pm.Pool(processes=n_jobs) as p:
        for _, _ in enumerate(p.imap_unordered(task, sample_names, 1)):
            pass
