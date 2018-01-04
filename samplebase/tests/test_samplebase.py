import unittest
import tempfile
import shutil
import numpy as np
import time

import samplebase as sb
import pathos.multiprocessing as pm


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
        sb.create_sample(self.tmp_prefix, args=args, name="sample")
        s = sb.Sample(self.tmp_prefix, name="sample")
        self.assertFalse(s.done)
        self.assertEqual(s.name, "sample")
        np.testing.assert_array_equal(s.args["y"], np.array([2., 3.]))
        self.assertEqual(s.args["x"], 2)
        self.assertEqual(s.result, {})
        s.result = {"blub": np.ones(2)}
        np.testing.assert_array_equal(s.result["blub"], np.ones(2))
        self.assertTrue(s.done)

    def test_scalar_args_and_result(self):
        args = {"x": 2, "y": 3}
        sb.create_sample(self.tmp_prefix, args=args, name="sample")
        s = sb.Sample(self.tmp_prefix, name="sample")
        self.assertFalse(s.done)
        self.assertIsNotNone(s.name)
        self.assertEqual(s.args, {"x": 2, "y": 3})
        self.assertEqual(s.result, {})

    def test_numpy_value_in_list(self):
        args = {"x": 10*[np.sqrt(2.)]}
        sb.create_sample(self.tmp_prefix, args=args, name="sample")
        s = sb.Sample(self.tmp_prefix, name="sample")
        self.assertAlmostEqual(s.args["x"][0], np.sqrt(2.))

    def test_numpy_arrays_in_list(self):
        rnd_arr = np.random.random(size=(10,10))
        args = {"x": 10*[rnd_arr]}
        sb.create_sample(self.tmp_prefix, args=args, name="sample")
        s = sb.Sample(self.tmp_prefix, name="sample")
        for i in range(10):
            np.testing.assert_array_equal(s.args["x"][i], rnd_arr)


class TestContextManager(TestSampleBase):
    def setUp(self):
        super(TestContextManager, self).setUp()

    def tearDown(self):
        super(TestContextManager, self).tearDown()

    def test_raise_if_being_processed(self):
        # +2 seconds of sleep
        def f(sample):
            time.sleep(2)

        prefix = self.tmp_prefix

        def task(name):
            with sb.SampleContextManager(prefix, name, raise_if_processing=True) as sample:
                f(sample)

        sb.create_sample(prefix, args={"x": 2}, name="sample")

        with self.assertRaises(FileExistsError):
            with pm.Pool(processes=3) as p:
                for _ in p.imap_unordered(task, ["sample", "sample", "sample"], 1):
                    pass


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
        sb.create_sample(self.tmp_prefix, args=args, name="samplename")
        sb.run_parallel(TestRun.f, self.tmp_prefix, ["samplename"])
        s = sb.Sample(self.tmp_prefix, "samplename")
        self.assertEqual(s.result["product"], "ypsilonypsilon")

    def test_sample_one_point_array(self):
        args = {"x": 2, "y": np.array([2., 3.])}
        sb.create_sample(self.tmp_prefix, args=args, name="samplename")
        sb.run_parallel(TestRun.f, self.tmp_prefix, ["samplename"])
        s = sb.Sample(self.tmp_prefix, name="samplename")
        np.testing.assert_array_equal(s.result["product"], np.array([4., 6.]))

    def test_sample_three_points_mixed(self):
        args = {"x": 2, "y": np.array([2., 3.])}
        sb.create_sample(self.tmp_prefix, args=args, name="samplename1")
        args = {"x": 2, "y": 3}
        sb.create_sample(self.tmp_prefix, args=args, name="samplename2")
        args = {"x": np.array([3., 3.]), "y": np.array([2., 2.])}
        sb.create_sample(self.tmp_prefix, args=args, name="samplename3")

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
        sb.create_sample(self.tmp_prefix, {"x": 2, "y": 3}, name="sam")
        sb.run_parallel(TestRun.f, self.tmp_prefix, ["sam", "sam", "sam", "sam", "sam"], n_jobs=5)
        s = sb.Sample(self.tmp_prefix, name="sam")
        self.assertEqual(s.result["product"], 6)

    def test_get_samples(self):
        for _ in range(100):
            sb.create_sample(self.tmp_prefix, args={"x": 2, "y": 3})
        names = sb.names_of_samples(self.tmp_prefix)
        sb.run_parallel(TestRun.f, self.tmp_prefix, names, n_jobs=4)
        samples = sb.list_of_samples(self.tmp_prefix)
        for i in range(100):
            self.assertEqual(samples[i].result["product"], 6)

    def test_multiply_four_times(self):
        def f(sample):
            sample.args["x"] = sample.args["x"] * 2

        sb.create_sample(self.tmp_prefix, {"x": 2, "y": 3}, name="sam")
        sb.process_parallel(f, self.tmp_prefix, ["sam", "sam", "sam", "sam"], n_jobs=4)
        s = sb.Sample(self.tmp_prefix, name="sam")
        self.assertEqual(s.args["x"], 32)

    def test_only_process_if_not_being_processed(self):
        # start 1 lengthy job, start another on the same sample, only if it is not being processed
        # thus in the end only one job has run
        # -> +2 seconds of sleep
        def f(sample):
            time.sleep(2)
            sample.args["x"] = sample.args["x"] * 2

        prefix = self.tmp_prefix

        def task(name):
            if not sb.Sample(prefix, name).being_processed:
                with sb.SampleContextManager(prefix, name) as sample:
                    f(sample)

        sb.create_sample(self.tmp_prefix, {"x": 2}, name="sam")

        with pm.Pool(processes=3) as p:
            for _ in p.imap_unordered(task, ["sam", "sam", "sam"], 1):
                pass

        s = sb.Sample(self.tmp_prefix, name="sam")
        self.assertEqual(s.args["x"], 4)


if __name__ == '__main__':
    unittest.main()
