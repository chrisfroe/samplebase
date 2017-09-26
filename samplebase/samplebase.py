# coding=utf-8

"""Sample results from an argument space. Handle and provide access to output files

In-process (server-less), file-local, ad-hoc, document-based database of samples/tasks
and parallel map() utility to process the samples. Each sample is an independent object handling
its own IO. This allows to trivially parallelise mapping a function onto a list of samples.
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
# possible: on _write() if value is point to a file,
# move this file to sample_dir and save this in storage data as {file: path}

# @todo time_it decorator for tasks, some log statements


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
