import os
import unittest
import tempfile
import shutil

import sampler


class TestSamplerBase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp_prefix = tempfile.mkdtemp("foo-prefix")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp_prefix)


class TestSamplerCtor(TestSamplerBase):
    def test_sanity(self):
        def f(x=None, y=None):
            return x * y

        sampler.Sampler("foo", self.tmp_prefix, f)
        self.assertTrue(os.path.exists(os.path.join(self.tmp_prefix, "foo")))


class TestSamplerMethods(TestSamplerBase):
    def test_add_scalar(self):
        raise RuntimeError("Impl this")

    def test_add_string(self):
        raise RuntimeError("Impl this")

    def test_add_array(self):
        raise RuntimeError("Impl this")


if __name__ == '__main__':
    unittest.main()
