#!/usr/bin/env bash
conda activate
which python
conda config --set always_yes true
conda update --all
conda install -q conda-build=3.16.2
conda clean --all -y
conda-build --version
conda install conda-verify
conda env list
