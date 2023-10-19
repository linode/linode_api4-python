#!/usr/bin/env python3
"""
A setuptools based setup module

Based on a template here:
https://github.com/pypa/sampleproject/blob/master/setup.py
"""
import os
# Always prefer setuptools over distutils
import sys
# To use a consistent encoding
from codecs import open
from os import path
from unittest import TestLoader

from setuptools import find_packages, setup

here = path.abspath(path.dirname(__file__))


def get_test_suite():
    test_loader = TestLoader()
    return test_loader.discover('test', pattern='*_test.py')


def get_baked_version():
    """
    Attempts to read the version from the baked_version file
    """
    with open("./baked_version", "r", encoding="utf-8") as f:
        result = f.read()

    return result


def bake_version(v):
    """
    Writes the given version to the baked_version file
    """
    with open("./baked_version", "w", encoding="utf-8") as f:
        f.write(v)


# Get the long description from the README file
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

# If there's already a baked version, use it rather than attempting
# to resolve the version from env.
# This is useful for installing from an SDist where the version
# cannot be dynamically resolved.
#
# NOTE: baked_version is deleted when running `make build` and `make install`,
# so it should always be recreated during the build process.
if path.isfile("baked_version"):
    version = get_baked_version()
else:
    # Otherwise, retrieve and bake the version as normal
    version = os.getenv("LINODE_SDK_VERSION", "0.0.0")
    bake_version(version)

if version.startswith("v"):
    version = version[1:]

setup(
    name='linode_api4',

    # Versions should comply with PEP440.  For a discussion on single-sourcing
    # the version across setup.py and the project code, see
    # https://packaging.python.org/en/latest/single_source_version.html
    version=version,

    description='The official python SDK for Linode API v4',
    long_description=long_description,
    long_description_content_type="text/x-rst",

    # The project's main homepage.
    url='https://github.com/linode/linode_api4-python',

    # Author details
    author='Linode',
    author_email='developers@linode.com',

    # Choose your license
    license='BSD 3-Clause License',

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 5 - Production/Stable',

        # Indicate who your project is intended for
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries',

        # Pick your license as you wish (should match "license" above)
        'License :: OSI Approved :: BSD License',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
    ],

    # What does your project relate to?
    keywords='linode cloud hosting infrastructure',

    # You can just specify the packages manually here if your project is
    # simple. Or you can use find_packages().
    packages=find_packages(exclude=['contrib', 'docs', 'test', 'test.*']),

    # What do we need for this to run
    python_requires=">=3.8",

    install_requires=[
        "requests",
        "polling"
    ],

    extras_require={
        "test": ["tox"],
    },
    test_suite='setup.get_test_suite'
)
