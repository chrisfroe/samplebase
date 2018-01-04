# coding=utf-8

"""Sample object hold data and handle IO"""

import os
import json
import numpy as np
import jsonpickle
import jsonpickle.ext.numpy as jsonpickle_numpy
import pickle
import logging

import samplebase.util as util
import samplebase.logutil as logutil

# to pickle numpy objects, which does not work outofthebox
jsonpickle_numpy.register_handlers()

log = logutil.StyleAdapter(logging.getLogger(__name__))

__all__ = ["SampleContextManager", "Sample", "Document"]


# @todo to make fully thread safe, let server distribute locks
# @todo how to check if write() has completed before unlocking/releasing?


class SampleContextManager(object):
    """
    Assure that only ever one user is processing the sample.
    Another user may read the sample but will only get the old state from file. Only when this manager
    exits, will the resulting state be written to file.
    """

    def __init__(self, prefix, name, raise_if_processing=False):
        self.s = None
        self.prefix = prefix
        self.name = name
        self.lockfile_path = os.path.join(self.prefix, self.name, self.name + ".processlock")
        self.raise_if_processing = raise_if_processing

    def __enter__(self):
        util.acquire_filelock(self.lockfile_path, raise_if_exists=self.raise_if_processing)
        self.s = Sample(self.prefix, name=self.name)
        return self.s

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.s._write()
        util.release_filelock(self.lockfile_path)


class Document(object):
    """
    Base class has data field, which is read from and written to 'data_path'. Accessory data is saved
    under 'prefix'. Read and write operations are thread-safe, if the same document on file is shared
    between multiple users.
    """

    def __init__(self, data_path, prefix):
        """Data path points to the main storage document"""
        self._data = None
        self._data_path = data_path
        self._prefix = prefix
        self._readwrite_lock = data_path + ".readwritelock"
        # @todo profile pickle vs json properly
        self._human_readable = True
        self._read()

    # @todo context manager
    def _write(self):
        util.acquire_filelock(self._readwrite_lock)
        storage_data = Document._convert_to_storage_data(self._data, self._prefix)
        if self._human_readable:
            with open(self._data_path, "w") as outfile:
                json.dump(storage_data, outfile)
                outfile.flush()
                os.fsync(outfile)
        else:
            with open(self._data_path, "wb") as outfile:
                pickle.dump(storage_data, outfile, pickle.HIGHEST_PROTOCOL)
                outfile.flush()
                os.fsync(outfile)
        util.release_filelock(self._readwrite_lock)

    def _read(self):
        util.acquire_filelock(self._readwrite_lock)
        if self._human_readable:
            with open(self._data_path, "r") as infile:
                storage_data = json.load(infile)
        else:
            with open(self._data_path, "rb") as infile:
                storage_data = pickle.load(infile)
        self._data = Document._convert_to_pure_data(storage_data, self._prefix)
        util.release_filelock(self._readwrite_lock)

    def __getitem__(self, item):
        return self._data[item]

    @staticmethod
    def _convert_to_storage_data(data, save_prefix):
        storage_data = dict()
        for key, value in data.items():
            if isinstance(value, str):
                storage_data[key] = {"value": value}
            elif isinstance(value, np.ndarray):
                file_name = key + util.stamp() + ".npy"
                file_path = os.path.join(save_prefix, file_name)
                np.save(file_path, value)
                storage_data[key] = {"ndarray": file_name}
            elif isinstance(value, dict):
                storage_data[key] = {"dict": Document._convert_to_storage_data(value, save_prefix)}
            elif not hasattr(value, "__len__"):
                storage_data[key] = {"value": value}
            else:
                # lists and unknown objects are json-pickled
                pickled = jsonpickle.encode(value)
                file_name = key + util.stamp() + ".json"
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
                pure_data[key] = Document._convert_to_pure_data(value["dict"], save_prefix)
            else:
                raise RuntimeError("Unknown storage data object with key " + key)
        return pure_data


class Sample(Document):
    """Specify Document. Introduce args, result, name and done"""

    def __init__(self, parent_prefix, name):
        """Specify a name to load an existing sample out of parent_prefix"""
        prefix = os.path.join(parent_prefix, name)
        data_path = os.path.join(prefix, name + ".json")
        super().__init__(data_path, prefix)

    @property
    def name(self):
        return self["name"]

    @property
    def done(self):
        return self["done"]

    @property
    def being_processed(self):
        process_lock_file_path = os.path.join(self._prefix, self.name + ".processlock")
        return os.path.isfile(process_lock_file_path)

    @property
    def args(self):
        return self["args"]

    @property
    def result(self):
        return self["result"]

    @result.setter
    def result(self, value):
        self._data["result"] = value
        self._data["done"] = True
