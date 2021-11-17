# -*- coding: utf-8 -*-

# Learn more: https://github.com/kennethreitz/setup.py

from setuptools import setup, find_packages


with open('README.md') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='heasoftpy',
    version='0.1.0',
    description='Python interface for Heasoft',
    long_description=readme,
    author='Abdu Zoghbi',
    author_email='abderahmen.zoghbi@nasa.gov',
    url='https://none',
    license=license,
    packages=find_packages(exclude=('tests', 'docs'))

)

