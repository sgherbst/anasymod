import os
import os.path
import shutil
import importlib

# working with paths

def get_full_path(path):
    return os.path.realpath(os.path.expanduser(path))

def get_sibling(path, sibling):
    return os.path.join(os.path.dirname(path), sibling)

# working with programs

def which(program, path=None):
    return get_full_path(shutil.which(program, path=path))

# working with packages

def module_top_dir(module_name):
    # import the module
    module = importlib.import_module(module_name)

    # find the full path to the module
    init_file_path = get_full_path(module.__file__)

    # go up two directories
    top_dir = os.path.dirname(os.path.dirname(init_file_path))

    # return the result
    return top_dir

def get_from_module(module_name, *args):
    # find top directory of module
    top_dir = module_top_dir(module_name)

    # construct full path
    return os.path.join(top_dir, *args)

# working with directories

def mkdir_p(path):
    os.makedirs(path, exist_ok=True)

def rm_rf(path):
    shutil.rmtree(path, ignore_errors=True)