from setuptools import setup, find_packages

setup(
    name='ip_core_gen',
    version='0.0.1',
    description='Generator for Xilinx IP cores custom to needs for msdsl package',
    url='',
    author='Gabriel Rutsch',
    author_email='gabriel.rutsch@infineon.com',
    packages=['ip_core_gen'],
    install_requires=[
        'jinja2'
    ],
    include_package_data=True,
    zip_safe=False,
)
