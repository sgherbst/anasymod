import os
import subprocess
import sys
import json

from math import ceil, log2
from collections import namedtuple
from anasymod.enums import ConfigSections

def back2fwd(path: str):
    return path.replace('\\', '/')

def call(args, cwd=None, wait=True):
    # set defaults
    if cwd is None:
        cwd = os.getcwd()

    # remember starting directory and change to cwd
    start_dir = os.getcwd()
    os.chdir(cwd)

    # run the command
    kwargs = dict(args=args, stdout=sys.stdout, stderr=sys.stdout)
    if wait:
        ret = subprocess.call(**kwargs)
        assert ret == 0
    else:
        subprocess.Popen(**kwargs)

    # change back to the starting directory
    os.chdir(start_dir)

def next_pow_2(x):
    return 2**int(ceil(log2(x)))

def read_config(cfg_file, section, subsection=None):
    """
    Return specified entries from config file, datatype is a dict. This dict will later be used to update flow configs.

    :param section: section to use from config file
    :param subsection: subsection to use from config file
    """
    if cfg_file is not None:
        if section in ConfigSections.__dict__.keys():
            if section in cfg_file:
                if subsection is not None:
                    return cfg_file[section].get(subsection)
                else:
                    return cfg_file.get(section)
        else:
            raise KeyError(f"provided section key:{section} is not supported")

def update_config(cfg: dict, config_section: dict):
    if config_section is not None:
        for k, v in config_section.items():
            if k in cfg:
                cfg[k] = v
            else:
                print(f"Warning: Processing config section:{config_section}; provided key: {k} does not exist in config")
    return cfg

########################
# JSON to object: from https://stackoverflow.com/questions/6578986/how-to-convert-json-data-into-a-python-object

def _json_object_hook(d):
    return namedtuple('X', d.keys())(*d.values())
def json2obj(data):
    return json.loads(data, object_hook=_json_object_hook)
########################

def main():
    print(next_pow_2(15))
    print(next_pow_2(16))
    print(next_pow_2(17))

if __name__ == '__main__':
    main()
