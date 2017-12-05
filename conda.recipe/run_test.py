import os
import sys
import nose

import samplebase

if __name__ == '__main__':
    target_dir = os.path.dirname(samplebase.__file__)
    exit_status = nose.run(argv=[sys.argv[0], target_dir, '-v'])
    print("nose returned exit_status: ", exit_status)
    sys.exit(0 if exit_status else 1)
