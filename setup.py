
from setuptools import setup, find_packages


with open('README.md') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

with open('heasoftpy/version.py') as f:
    version = f.read()

setup(
    name='heasoftpy',
    version=version,
    description='Python interface for Heasoft',
    long_description=readme,
    author='Abdu Zoghbi',
    author_email='abderahmen.zoghbi@nasa.gov',
    url='https://none',
    license=license,
    packages=find_packages(exclude=('tests', 'docs'))

)

