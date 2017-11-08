# coding=utf-8
from setuptools import setup, find_packages
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

    zip_safe=True,

    author="Christoph Fröhner",
    author_email="christoph.froehner@fu-berlin.de",
    description="Document-based, serverless, threadsafe (as possible) database to "
                "easily perform a task in parallel on many samples",
    license="LGPL",
    url="https://github.com/chrisfroe/samplebase",
)
