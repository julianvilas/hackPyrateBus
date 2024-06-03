import os

from setuptools import setup, find_packages

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "hackPyrateBus",
    version = '0.0.6',
    python_requires='>=3.11',
    description = ("Python library with high-level functions to interact with specific ICs using Bus Pirate"),
    license = "GPLv3",
    keywords = "BusPirate",
    url = "https://github.com/julianvilas/hackPyrateBus",
    # NOTE: the pyBusPirateLite dependency is vendored from
    # https://github.com/julianvilas/pyBusPirateLite/tree/new for convenience,
    # as the project does not seem to be maintained and it is not available in
    # PyPI.  Again many thanks to the original author!
    packages=find_packages(),
    install_requires=[
        'pyserial',
    ],
    long_description=read('README.md'),
    long_description_content_type='text/markdown',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python :: 3.12',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
