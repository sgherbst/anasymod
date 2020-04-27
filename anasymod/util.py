# general imports
import os
import os.path
import sys
import json
import shlex
import re
from multiprocessing.pool import ThreadPool
from math import ceil, log2
from collections import namedtuple
from argparse import ArgumentParser
from subprocess import Popen, PIPE, STDOUT
from glob import glob
from typing import Union, Pattern

# msdsl imports
from msdsl.generator.verilog import VerilogGenerator


def back2fwd(path: str):
    return path.replace('\\', '/')

def error_detected(text, err_str):
    # Returns True if the error pattern "err_str" is detected in "text"
    # "err_str" can be a one of several things:
    # 1. A single string.
    # 2. A list of strings.  The error is considered to be found if any of the
    #    strings appear in the given text.
    # 3. A regular expression Pattern (re.Pattern).  The given text is searched
    #    for any occurrence of this pattern.
    # from: https://github.com/leonardt/fault/blob/master/fault/subprocess_run.py
    if isinstance(err_str, str):
        return err_str in text
    elif isinstance(err_str, list):
        return any(elem in text for elem in err_str)
    elif isinstance(err_str, Pattern):
        return err_str.match(text) is not None
    else:
        raise Exception(f'Invalid err_str: {err_str}.')

def tee_output(fd, err_str=None):
    # prints lines from the given file descriptor while checking for errors
    # returns a flag indicating whether an error was detected
    # modified from: https://github.com/leonardt/fault/blob/master/fault/subprocess_run.py
    found_err = False
    for line in fd:
        # display line
        print(line, end='')
        # check line for errors
        if err_str is not None:
            if error_detected(text=line, err_str=err_str):
                found_err = True
    # Return flag indicating whether an error was found
    return found_err

def call(args, cwd=None, wait=True, err_str=None):
    # run a command and optionally check for error strings in the output
    # modified from: https://github.com/leonardt/fault/blob/master/fault/subprocess_run.py
    # print command string with proper escaping so that
    # a user can simply copy and paste the command to re-run it
    cmd_str = ' '.join(shlex.quote(arg) for arg in args)
    print(f"Checking return code of subprocess call: {cmd_str}")
    # run the command
    if wait:
        with Popen(args, cwd=cwd, stdout=PIPE, stderr=STDOUT, bufsize=1,
                   universal_newlines=True) as p:
            # print output while checking for errors
            found_err = tee_output(fd=p.stdout, err_str=err_str)

            # get return code and check result if desired
            returncode = p.wait()

            # check return code
            assert returncode == 0, f'Exited with non-zero code: {returncode}'

            # check for an error in the output text
            if found_err:
                raise Exception(f'Found {err_str} in output of subprocess.')
    else:
        Popen(args=args, cwd=cwd, stdout=sys.stdout, stderr=sys.stdout)


def next_pow_2(x):
    '''
    Return y such that 2**y >= x
    '''
    return 2**int(ceil(log2(x)))

def expand_searchpaths(paths: Union[list, str], rel_path_reference: str):
    abs_paths = []

    if isinstance(paths, str):
        paths = [paths]
    elif isinstance(paths, list):
        pass
    else:
        raise TypeError(f"Wrong format used for passing searchpaths, expecting list: {paths}")
    for file in paths:
        file = os.path.expandvars(str(file).strip('" '))
        if not os.path.isabs(file):
            if rel_path_reference is not None:
                path_suffix = file.replace('\\', '/').replace('/', os.sep).split(os.sep)
                try:
                    path_suffix.remove('.')
                except:
                    pass
                file = os.path.join(rel_path_reference, *(path_suffix))
            else:
                raise KeyError(f"No reference for expanding relative paths was provided for search paths: {paths}")
        abs_paths.append(file)

    return [file for p in abs_paths for file in glob(p)]

########################
# parallel_scripts
# ref: https://stackoverflow.com/questions/26774781/python-multiple-subprocess-with-a-pool-queue-recover-output-as-soon-as-one-finis

def parallel_calls(calls, num=None):
    tp = ThreadPool(num)

    for arg_list in calls:
        tp.apply_async(call, (arg_list,))

    tp.close()
    tp.join()

########################
# file_len: modified from https://stackoverflow.com/questions/845058/how-to-get-line-count-cheaply-in-python

def file_len(fname):
    with open(fname, encoding='utf-8') as f:
        i = 0

        for i, l in enumerate(f, 1):
            pass

        return i


def vivado_search_key(dir_):
    '''
    Determine the year and version of a Vivado install directory.
    '''
    year, version = os.path.basename(dir_).split('.')
    year, version = int(year), int(version)

    return -year, -version

########################
# JSON to object: from https://stackoverflow.com/questions/6578986/how-to-convert-json-data-into-a-python-object

def _json_object_hook(d):
    return namedtuple('X', d.keys())(*d.values())
def json2obj(data):
    return json.loads(data, object_hook=_json_object_hook)
########################


# Argument parser for the examples
class ExampleControl:
    def __init__(self):
        # create the parser
        parser = ArgumentParser()

        # add custom arguments
        parser.add_argument('-o', '--output', type=str)
        parser.add_argument('--dt', type=float)

        # parser arguments
        args = parser.parse_args()

        # save arguments
        self.output = os.path.realpath(os.path.expanduser(args.output))
        self.dt = args.dt

    def write_model(self, model):
        # determine the filename
        filename = os.path.join(self.output, f'{model.module_name}.sv')
        print('Model will be written to: ' + filename)

        # write the model to a file
        model.compile_to_file(VerilogGenerator(), filename)


def main():
    print(next_pow_2(15))
    print(next_pow_2(16))
    print(next_pow_2(17))


if __name__ == '__main__':
    main()
