# coding=utf-8

"""Sample object holds data and handles IO"""

import os
import json
import jsonpickle
import numpy as np

import samplebase.util as util


class DocumentBase(object):
    """
    Base class has data field, which is read from and written to 'data_path'. Accessory data is saved
    under 'prefix'
    """

    def __init__(self, data_path, prefix):
        """Data path points to the main storage document, which is contained in the directory 'prefix' """
        self._data = None
        self._data_path = data_path
        self._prefix = prefix
        self._outdated = True

    def write(self):
        storage_data = DocumentBase._convert_to_storage_data(self._data, self._prefix)
        with open(self._data_path, "w") as outfile:
            json.dump(storage_data, outfile)

    def read(self):
        with open(self._data_path, "r") as infile:
            storage_data = json.load(infile)
        self._data = DocumentBase._convert_to_pure_data(storage_data, self._prefix)
        self._outdated = False

    def __getitem__(self, item):
        if self._outdated:
            self.read()
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
                storage_data[key] = {"dict": DocumentBase._convert_to_storage_data(value, save_prefix)}
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
                # @todo instead of loadings arrays place CachedArrays at the corresponding locations
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
                pure_data[key] = DocumentBase._convert_to_pure_data(value["dict"], save_prefix)
            else:
                raise RuntimeError("Unknown storage data object with key " + key)
        return pure_data


class Sample(DocumentBase):
    """Currently read and write operations should be done manually"""

    def __init__(self, parent_prefix, name=None, args=None):
        if not ((name is not None) or (args is not None)):
            raise RuntimeError("Either name or initial arguments (or both) must be given.")
        if args is None:
            args = dict()
        if name is None:
            name = util.stamp()
        prefix = os.path.join(parent_prefix, name)
        data_path = os.path.join(prefix, name + ".json")
        super().__init__(data_path, prefix)
        if not os.path.exists(self._prefix):
            os.makedirs(self._prefix, exist_ok=False)

        if not os.path.exists(self._data_path):
            self._data = {
                "name": name,
                "done": False,
                "args": args,
                "result": {}
            }
            self.write()

    @property
    def name(self):
        return self["name"]

    @property
    def done(self):
        return self["done"]

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
        self.write()
