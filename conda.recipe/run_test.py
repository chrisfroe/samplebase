import os
import sys
import nose

import samplebase


def run_nose(verbose=False):
    initial_dir = os.getcwd()
    samplebase_file = os.path.abspath(samplebase.__file__)
    samplebase_dir = os.path.dirname(samplebase_file)
    nose_argv = sys.argv
    nose_argv += ['--detailed-errors', '--exe']
    if verbose:
        nose_argv.append('-v')
        print("initial_dir", initial_dir)
        print("samplebase_file", samplebase_file)
        print("samplebase_dir", samplebase_dir)
    os.chdir(samplebase_dir)
    try:
        exit_status = nose.run(argv=nose_argv)
    finally:
        os.chdir(initial_dir)
    return exit_status


if __name__ == '__main__':
    print("run_test .. ")
    exit_status = run_nose(verbose=True)
    print("nose returned exit_status: ", exit_status)
    sys.exit(0 if exit_status else 1)
