# coding=utf-8

"""Sample results from an argument space. Handle and provide access to output files

In-process (server-less), file-local, ad-hoc, document-based database of samples/tasks
and parallel map() utility to process the samples. Each sample is an independent object handling
its own IO. This allows to trivially parallelise mapping a function onto a list of samples, but
means careful reading and writing. If samples are only processed with the utilities, everything should
be fine.
"""

import os
import logging
import pathos.multiprocessing as pm

import samplebase.util as util
from samplebase.sample import Sample

__license__ = "LGPL"
__author__ = "chrisfroe"

logging.basicConfig(format='[sampler] [%(asctime)s] [%(levelname)s] %(message)s', level=logging.INFO,
                    datefmt="%Y-%m-%d %H:%M:%S")
log = util.StyleAdapter(logging.getLogger(__name__))


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


def list_of_samples(samples_dir=os.getcwd()):
    samples = []
    with os.scandir(samples_dir) as it:
        for sample in it:
            if sample.is_dir():
                samples.append(Sample(samples_dir, sample.name))
    return samples


def run(func, samples, n_jobs=1):
    """Map func on args to get results. Only process sample if it is not done."""

    def task(sample):
        sample.result = func(**sample.args)

    todo_samples = [s for s in samples if not s.done]

    with pm.Pool(processes=n_jobs) as p:
        for _, _ in enumerate(p.imap_unordered(task, todo_samples, 1)):
            pass

    for s in todo_samples:
        s._outdated = True


def run_task(func, samples, n_jobs=1):
    """Similar to run, but map func on samples, to do whatever. Useful for pre/post processing of args or results"""

    def task(sample):
        func(sample)
        sample.write()

    with pm.Pool(processes=n_jobs) as p:
        for _, _ in enumerate(p.imap_unordered(task, samples, 1)):
            pass

    for s in samples:
        s._outdated = True
