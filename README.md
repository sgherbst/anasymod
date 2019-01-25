* Requirements

1. Python
2. Vivado
3. GTKwave

* Installation

1. Open a terminal and navigate to a convenient directory.
```shell
> git clone ssh://git@bitbucket.vih.infineon.com:7999/inicio/anasymod.git --recursive
```

2. Install all of the Python packages in the project:
```shell
> cd ip_core_gen
> pip install -e .
> cd ..
> cd emuflow
> pip install -e .
> cd ..
> cd msdsl
> pip install -e .
> cd ..
> cd svreal
> pip install -e .
> cd ..
```

3. Have a look at anasymod/test_project/build_system/includes.mk.  In particular, update the paths to Python, Vivado, and GTKwave as necessary.