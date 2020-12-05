import os
from shutil import which
from anasymod.util import call

def run_plugin():
    if 'PYTHON_MSDSL' in os.environ:
        python_name = os.environ['PYTHON_MSDSL']
    else:
        python_name = which('python')

    print('*** PYTHON_NAME ***')
    print(python_name)
    print('*** PYTHON_CALL ***')
    call([python_name, '-c',
          "from pathlib import Path;"
          "a=Path('a\\\\b\\\\c');"
          "print(type(a));"
          "print(a);"
          "print(a.as_posix())"
    ])