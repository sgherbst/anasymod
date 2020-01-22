from setuptools import setup, find_packages

name = 'anasymod'
version = '0.1.8'

DESCRIPTION = '''\
Tool for running mixed-signal emulations on FPGAs\
'''

with open('README.md', 'r') as fh:
    LONG_DESCRIPTION = fh.read()

setup(
    name=name,
    version=version,
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    long_description_content_type='text/markdown',
    keywords = ['analog', 'mixed-signal', 'mixed signal', 'vivado',
                'xcelium', 'iverilog', 'icarus-verilog', 'icarus verilog',
                'generator', 'verilog', 'system-verilog', 'system verilog',
                'emulation', 'fpga'],
    packages=find_packages(),
    entry_points = {
        'console_scripts': [
            'anasymod=anasymod.analysis:main'
        ]
    },
    install_requires=[
        'svreal>=0.1.9',
        'msdsl>=0.1.6',
        'jinja2',
        'pyvcd',
        'pyserial'
    ],
    license='BSD 3-Clause "New" or "Revised" License',
    url=f'https://github.com/sgherbst/{name}',
    author='Gabriel Rutsch, Steven Herbst, Shivani Saravanan',
    author_email='gabriel.rutsch@infineon.com',
    python_requires='>=3.7',
    download_url = f'https://github.com/sgherbst/{name}/archive/v{version}.tar.gz',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Scientific/Engineering :: Electronic Design Automation (EDA)',
        'License :: OSI Approved :: BSD License',
        f'Programming Language :: Python :: 3.7'
    ],
    include_package_data=True,
    zip_safe=False
)
