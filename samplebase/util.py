# coding=utf-8

import os
import logging
import time
import random
import string

import samplebase.logutil as logutil

log = logutil.StyleAdapter(logging.getLogger(__name__))

__license__ = "LGPL"
__author__ = "chrisfroe"


def stamp(random_digits=8):
    """
    Generate a string based on the current date, time and an 8-digit
    random string, which shall be guarantee enough not to generate the same string twice
    """
    timestamp = time.strftime("%Y_%m_%d-%H_%M_%S")
    randomstamp = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(random_digits))
    _stamp = timestamp + "_" + randomstamp
    return _stamp


def acquire_filelock(lock_path, time_out_seconds=1):
    acquired = False
    while not acquired:
        try:
            with open(lock_path, "x"):
                os.utime(lock_path, None)
        except FileExistsError:
            log.info("Could not acquire lock, wait for {} s", time_out_seconds)
            time.sleep(time_out_seconds)
        else:
            acquired = True


def release_filelock(lock_path):
    os.remove(lock_path)
