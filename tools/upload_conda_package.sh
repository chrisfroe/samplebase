#!/usr/bin/env bash

set -e -u

function set_this_up {
    if [ "$TRAVIS_PULL_REQUEST" != "false" ]
    then
        echo "This was a pull request, thus dont upload package. Exit."
        exit 0
    fi
    if [ "$TRAVIS_BRANCH" != "master" ]
    then
        echo "This commit was made against the $TRAVIS_BRANCH branch and not the master branch. Exit."
        exit 0
    fi
    if [ -z ${BINSTAR_TOKEN+x} ]
    then
      echo "BINSTAR_TOKEN was not set, so this is probably a fork. Exit."
      exit 0
    fi
}


set_this_up

CONDA_PACKAGE_FILE=$(conda build conda.recipe --output)
echo "found conda package file $CONDA_PACKAGE_FILE"

conda install anaconda-client -qy
anaconda -t $BINSTAR_TOKEN upload -u chrisfroe --force $CONDA_PACKAGE_FILE
