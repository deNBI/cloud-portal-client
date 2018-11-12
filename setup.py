#!/usr/bin/env python
# encoding: utf-8
import os
from setuptools import find_packages, setup

with open(os.path.join(os.path.dirname(__file__), 'README.md')) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name='cloud-portal-client',
    version='0.1',
    packages=find_packages(),
    include_package_data=True,
    license='Apache License 2.0',
    description='The Cloud Portal Client is a client written in Python which provides functions to create virtual machines in an OpenStack project..',
    long_description=README,
    author='Sören Giller, David Weinholz',
    install_requires = requirements,
    zip_safe = False,
    classifiers=[
        'Environment :: OpenStack'
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
)