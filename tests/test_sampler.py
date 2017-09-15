import os
import unittest
import tempfile
import shutil
import json

import sampler


class TestSamplerBase(unittest.TestCase):
    tmp_prefix = None

    @classmethod
    def setUpClass(cls):
        cls.tmp_prefix = tempfile.mkdtemp("foo-prefix")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp_prefix)


class TestSamplerFileSpecification(TestSamplerBase):
    """Add input values and assert for the saved json. Assume the file specification."""
    s = None

    def setUp(self):
        def f(x=None, y=None):
            return x * y

        self.s = sampler.Sampler("foo", self.tmp_prefix, f)

    def test_add_scalar(self):
        args = {"x": 2, "y": "ypsilon"}
        self.s.add(args, "samplename")
        with open(os.path.join(self.s.samples_dir, "samplename", "samplename.json")) as json_file:
            loaded = json.load(json_file)
        self.assertTrue(isinstance(loaded, dict))
        self.assertEqual(loaded["name"], "samplename")
        self.assertEqual(loaded["done"], False)
        self.assertTrue("args" in loaded)
        self.assertEqual(loaded["args"]["x"]["value"], 2)
        self.assertEqual(loaded["args"]["y"]["value"], "ypsilon")

    def test_add_array(self):
        raise RuntimeError("impl this")


class TestSamplerMethods(TestSamplerBase):
    """
    Test methods like add() using the according read() methods.
    Do not assume the file specification, but assume that samples lie
    within some directory.
    """
    s = None

    def setUp(self):
        def f(x=None, y=None):
            return x * y

        self.s = sampler.Sampler("foo", self.tmp_prefix, f)

    def test_ctor(self):
        self.assertTrue(os.path.exists(os.path.join(self.tmp_prefix, "foo")))

    def test_sample(self):
        # add args
        # sample
        # read results
        raise RuntimeError("impl this")

    def test_remove(self):
        args = {"x": 2, "y": "ypsilon"}
        self.s.add(args, "samplename")
        self.s.remove("samplename")
        self.assertTrue(not os.path.exists(os.path.join(self.s.samples_dir, "samplename")))

    def test_remove_if_true(self):
        args = {"x": 2, "y": "ypsilon"}
        self.s.add(args, "samplename")
        self.s.remove_if(lambda x: x["args"]["x"] == "samplename")
        self.assertTrue(not os.path.exists(os.path.join(self.s.samples_dir, "samplename")))

    def test_remove_if_false(self):
        args = {"x": 2, "y": "ypsilon"}
        self.s.add(args, "samplename")
        self.s.remove_if(lambda x: x["args"]["x"] == "Anothername")
        self.assertTrue(os.path.exists(os.path.join(self.s.samples_dir, "samplename")))


if __name__ == '__main__':
    unittest.main()
