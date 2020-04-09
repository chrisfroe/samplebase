#!/bin/bash
unset MACOSX_DEPLOYMENT_TARGET

# set version within the source code
echo "__version__ = '${PKG_VERSION}_${PKG_BUILDNUM}'" | tee samplebase/version.py

${PYTHON} setup.py install;
