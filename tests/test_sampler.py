import os
import unittest
import tempfile
import shutil
import json
import numpy as np

import sampler


class TestSamplerBase(unittest.TestCase):
    tmp_prefix = None

    def setUp(self):
        self.tmp_prefix = tempfile.mkdtemp("foo-prefix")

    def tearDown(self):
        shutil.rmtree(self.tmp_prefix)


class TestSamplerFileSpecification(TestSamplerBase):
    """Add input values and assert for the saved json. Assume the file specification."""
    s = None

    def setUp(self):
        super(TestSamplerFileSpecification, self).setUp()

        def f(x=None, y=None):
            return {"product": x * y}

        self.s = sampler.Sampler("foo", self.tmp_prefix, f)

    def tearDown(self):
        super(TestSamplerFileSpecification, self).tearDown()

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
        args = {"x": 2, "y": np.array([2., 3.])}
        self.s.add(args, "samplename")
        with open(os.path.join(self.s.samples_dir, "samplename", "samplename.json")) as json_file:
            loaded = json.load(json_file)
        self.assertEqual(loaded["name"], "samplename")
        self.assertEqual(loaded["done"], False)
        self.assertTrue("args" in loaded)
        self.assertTrue("y" in loaded["args"])
        self.assertTrue("file" in loaded["args"]["y"])
        relative_path = loaded["args"]["y"]["file"]
        self.assertTrue(isinstance(relative_path, str))
        self.assertTrue("args/" in relative_path)
        file_path = os.path.join(self.s.samples_dir, "samplename", os.path.normpath(relative_path))
        arr = np.load(file_path)
        np.testing.assert_array_equal(arr, np.array([2., 3.]))


class TestSamplerMethods(TestSamplerBase):
    """
    Test methods like add() using the according read() methods.
    Do not assume the file specification, but assume that samples lie
    within some directory.
    """
    s = None

    def setUp(self):
        super(TestSamplerMethods, self).setUp()

        def f(x=None, y=None):
            return {"product": x * y}

        self.s = sampler.Sampler("foo", self.tmp_prefix, f)

    def tearDown(self):
        super(TestSamplerMethods, self).tearDown()

    def test_ctor(self):
        self.assertTrue(os.path.exists(os.path.join(self.tmp_prefix, "foo")))

    def test_sample_one_point_scalar(self):
        args = {"x": 2, "y": "ypsilon"}
        self.s.add(args, "samplename")
        self.s.sample()
        result = self.s.result("samplename")
        self.assertEqual(result["product"], "ypsilonypsilon")

    def test_sample_one_point_array(self):
        args = {"x": 2, "y": np.array([2., 3.])}
        self.s.add(args, "samplename")
        self.s.sample()
        result = self.s.result("samplename")
        np.testing.assert_array_equal(result["product"], np.array([4., 6.]))

    def test_sample_three_points_mixed(self):
        args = {"x": 2, "y": np.array([2., 3.])}
        self.s.add(args, "samplename1")
        args = {"x": 2, "y": 3}
        self.s.add(args, "samplename2")
        args = {"x": np.array([3., 3.]), "y": np.array([2., 2.])}
        self.s.add(args, "samplename3")
        self.s.sample(n_jobs=3)
        result1 = self.s.result("samplename1")
        np.testing.assert_array_equal(result1["product"], np.array([4., 6.]))
        result2 = self.s.result("samplename2")
        self.assertEqual(result2["product"], 6)
        result3 = self.s.result("samplename3")
        np.testing.assert_array_equal(result3["product"], np.array([6., 6.]))

    def test_remove(self):
        args = {"x": 2, "y": "ypsilon"}
        self.s.add(args, "samplename")
        self.s.remove("samplename")
        self.assertTrue(not os.path.exists(os.path.join(self.s.samples_dir, "samplename")))

    def test_remove_if_true(self):
        args = {"x": 2, "y": "ypsilon"}
        self.s.add(args, "samplename")
        self.s.remove_if(lambda x: x["args"]["x"] == 2)
        self.assertTrue(not os.path.exists(os.path.join(self.s.samples_dir, "samplename")))

    def test_remove_if_false(self):
        args = {"x": 2, "y": "ypsilon"}
        self.s.add(args, "samplename")
        self.s.remove_if(lambda x: x["args"]["x"] == 3)
        self.assertTrue(os.path.exists(os.path.join(self.s.samples_dir, "samplename")))


if __name__ == '__main__':
    unittest.main()
