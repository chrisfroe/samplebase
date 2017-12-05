# coding=utf-8
from setuptools import setup, find_packages
from distutils.util import convert_path
from codecs import open
import os


def read(fname):
    path = os.path.join(os.path.dirname(__file__), fname)
    return open(path, encoding='utf-8').read()


# This will set the version string to __version__
exec(read('samplebase/version.py'))

setup(
    name="samplebase",
    version=__version__,
    packages=find_packages(),
    zip_safe=False,
    author="Christoph Fröhner",
    author_email="christoph.froehner@fu-berlin.de",
    description="Document-based, serverless, threadsafe (as possible) database "
                "with utilities to easily perform a task on many samples in parallel",
    license="LGPL",
    url="https://github.com/chrisfroe/samplebase",
)
