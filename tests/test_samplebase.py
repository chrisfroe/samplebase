import unittest
import tempfile
import shutil
import numpy as np

import samplebase as sb


class TestSampleBase(unittest.TestCase):
    tmp_prefix = None

    def setUp(self):
        self.tmp_prefix = tempfile.mkdtemp("foo-prefix")

    def tearDown(self):
        shutil.rmtree(self.tmp_prefix)


class TestSample(TestSampleBase):
    def setUp(self):
        super(TestSample, self).setUp()

    def tearDown(self):
        super(TestSample, self).tearDown()

    def test_array_args_and_result(self):
        args = {"x": 2, "y": np.array([2., 3.])}
        s = sb.Sample(self.tmp_prefix, args=args, name="smpl")
        self.assertFalse(s.done)
        self.assertEqual(s.name, "smpl")
        np.testing.assert_array_equal(s.args["y"], np.array([2., 3.]))
        self.assertEqual(s.args["x"], 2)
        self.assertEqual(s.result, {})
        s.result = {"blub": np.ones(2)}
        np.testing.assert_array_equal(s.result["blub"], np.ones(2))
        self.assertTrue(s.done)

    def test_scalar_args_and_result(self):
        args = {"x": 2, "y": 3}
        s = sb.Sample(self.tmp_prefix, args=args)
        self.assertFalse(s.done)
        self.assertIsNotNone(s.name)
        self.assertEqual(s.args, {"x": 2, "y": 3})
        self.assertEqual(s.result, {})

    def test_another_sample_object_same_file(self):
        s1 = sb.Sample(self.tmp_prefix, args={"x": 42}, name="datsample")
        s2 = sb.Sample(self.tmp_prefix, name="datsample")
        self.assertEqual(s2.args, {"x": 42})


class TestRun(TestSampleBase):
    @staticmethod
    def f(x=None, y=None):
        return {"product": x * y}

    def setUp(self):
        super(TestRun, self).setUp()

    def tearDown(self):
        super(TestRun, self).tearDown()

    def test_sample_one_point_scalar(self):
        args = {"x": 2, "y": "ypsilon"}
        sb.Sample(self.tmp_prefix, name="samplename", args=args)
        sb.run_parallel(TestRun.f, self.tmp_prefix, ["samplename"])
        s = sb.Sample(self.tmp_prefix, "samplename")
        self.assertEqual(s.result["product"], "ypsilonypsilon")

    def test_sample_one_point_array(self):
        args = {"x": 2, "y": np.array([2., 3.])}
        sb.Sample(self.tmp_prefix, name="samplename", args=args)
        sb.run_parallel(TestRun.f, self.tmp_prefix, ["samplename"])
        s = sb.Sample(self.tmp_prefix, name="samplename")
        np.testing.assert_array_equal(s.result["product"], np.array([4., 6.]))

    def test_sample_three_points_mixed(self):
        args = {"x": 2, "y": np.array([2., 3.])}
        sb.Sample(self.tmp_prefix, name="samplename1", args=args)
        args = {"x": 2, "y": 3}
        sb.Sample(self.tmp_prefix, name="samplename2", args=args)
        args = {"x": np.array([3., 3.]), "y": np.array([2., 2.])}
        sb.Sample(self.tmp_prefix, name="samplename3", args=args)

        sb.run_parallel(TestRun.f, self.tmp_prefix, ["samplename1", "samplename2", "samplename3"], n_jobs=3)

        s1 = sb.Sample(self.tmp_prefix, name="samplename1")
        self.assertEqual(s1.name, "samplename1")
        np.testing.assert_array_equal(s1.result["product"], np.array([4., 6.]))
        s2 = sb.Sample(self.tmp_prefix, name="samplename2")
        self.assertEqual(s2.name, "samplename2")
        self.assertEqual(s2.result["product"], 6)
        s3 = sb.Sample(self.tmp_prefix, name="samplename3")
        self.assertEqual(s3.name, "samplename3")
        np.testing.assert_array_equal(s3.result["product"], np.array([6., 6.]))

    def test_run_parallel_on_same_sample(self):
        sb.Sample(self.tmp_prefix, name="sam", args={"x": 2, "y": 3})
        sb.run_parallel(TestRun.f, self.tmp_prefix, ["sam", "sam", "sam", "sam", "sam"], n_jobs=5)


# @todo test get_list_of_samples
# @todo case where same file is processed by one thread and read by another at the same time,
# i.e. there exist two instances of Sample pointing to the same file

if __name__ == '__main__':
    unittest.main()
