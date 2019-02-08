from setuptools import setup

setup(
    name='anasymod',
    version='0.0.1',
    description='Vivado automation flow for running mixed-signal emulations on FPGAs',
    url='https://bitbucket.vih.infineon.com/scm/inicio/anasymod.git',
    author='Gabriel Rutsch, Steven Herbst, Shivani Saravanan',
    author_email='gabriel.rutsch@infineon.com, sherbst@stanford.edu, shivani.saravanan@infineon.com',
    packages=['anasymod'],
    install_requires=[
        'jinja2'
    ],
    include_package_data=True,
    zip_safe=False,
)
