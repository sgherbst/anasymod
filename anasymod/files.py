import os
import os.path
from pathlib import Path
import shutil

# working with paths

def get_full_path(path):
    return str(Path(path).resolve())

def get_sibling(path, sibling):
    return str(Path(path).parent / sibling)

# working with programs

def which(program, path=None):
    return get_full_path(shutil.which(program, path=path))

# working with packages

def get_from_anasymod(*args):
    return os.path.join(str(Path(__file__).parent), *args)

# working with directories

def mkdir_p(path):
    Path(path).mkdir(parents=True, exist_ok=True)

def rm_rf(path):
    shutil.rmtree(path, ignore_errors=True)
