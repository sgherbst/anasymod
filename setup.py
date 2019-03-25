from setuptools import setup

setup(
    name='anasymod',
    version='0.0.1',
    description='Vivado automation flow for running mixed-signal emulations on FPGAs',
    url='https://github.com/sgherbst/anasymod.git',
    author='Gabriel Rutsch, Steven Herbst, Shivani Saravanan',
    author_email='gabriel.rutsch@infineon.com, sherbst@stanford.edu, shivani.saravanan@infineon.com',
    packages=['anasymod'],
    install_requires=[
        'jinja2',
        'pyvcd'
    ],
    scripts=['scripts/anasymod'],
    include_package_data=True,
    zip_safe=False,
)
