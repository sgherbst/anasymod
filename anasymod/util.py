import os
import subprocess
import sys
import json

from math import ceil, log2
from collections import namedtuple

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


########################
# JSON to object: from https://stackoverflow.com/questions/6578986/how-to-convert-json-data-into-a-python-object
def _json_object_hook(d):
    return namedtuple('X', d.keys())(*d.values())
def json2obj(data):
    return json.loads(data, object_hook=_json_object_hook)
########################

class DictObject:
    '''
    @DynamicAttrs
    '''

    def __init__(self, filename):
        for key, val in d.items():
            setattr(self, key, val)

    @staticmethod
    def load_json(filename):
        with open(filename, 'r') as f:
            d = json.load(f)

        return DictObject(d)

def main():
    print(next_pow_2(15))
    print(next_pow_2(16))
    print(next_pow_2(17))

    print(DictObject({'a': 42}).a)

if __name__ == '__main__':
    main()