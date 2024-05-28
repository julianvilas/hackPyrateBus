import os

from setuptools import setup

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "bphelpers",
    version = "0.0.1",
    python_requires='>=3.11',
    description = ("Python library with high-level functions to interact with specific ICs using Bus Pirate"),
    license = "GPLv3",
    keywords = "BusPirate",
    url = "https://github.com/julianvilas/bphelpers",
    packages=['bphelpers'],
    long_description=read('README.md'),
    # NOTE: for convenience the pyBusPirateLite dependency is installed from a
    # forked repository as the original one is not updated
    install_requires=['pyBusPirateLite @ https://github.com/julianvilas/pyBusPirateLite/tarball/master'],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python :: 3.6',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
