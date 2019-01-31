import os
import subprocess
import sys

from math import ceil, log2

def back2fwd(path: str):
    return path.replace('\\', '/')

def call(args, cwd=None):
    # set defaults
    if cwd is None:
        cwd = os.getcwd()

    # remember starting directory and change to cwd
    start_dir = os.getcwd()
    os.chdir(cwd)

    # run the command
    ret = subprocess.call(args=args, stdout=sys.stdout, stderr=sys.stdout)
    assert ret == 0

    # change back to the starting directory
    os.chdir(start_dir)

def next_pow_2(x):
    return 2**int(ceil(log2(x)))

def main():
    print(next_pow_2(15))
    print(next_pow_2(16))
    print(next_pow_2(17))

if __name__ == '__main__':
    main()