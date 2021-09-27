#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name='podman_python_api',
    version='0.0.1',
    description='podman api python wrapper',
    author='Andreas Schwalb',
    author_email='andy@cyber-home.net',
    url='https://github.com/AndreasSchwalb/podman_python_api.git',
    packages=find_packages(where='./src', include=('*')),
    install_requires=[
        'python-dotenv>=0.19.0',
        'requests>=2.26.0',
        'requests-unixsocket>=0.2.0'
    ],
    package_dir={"": "src"},
    zip_safe=False
)
