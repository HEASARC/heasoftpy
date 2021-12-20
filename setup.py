
from setuptools import setup, find_packages
from setuptools.command.install import install
from setuptools.command.build_py import build_py
from distutils.command.clean import clean
import os
import sys


class HSPInstallCommand(build_py):
    """Run install.py before doing the standard install"""
    def run(self):
        # add current dir to path to import (or call) install.py
        # install.py will fail is HEADAS is not initialized
        sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
        import install as hspinstall
        super().run()

class HSPCleanCommand(clean):
    """Custom clean command that removes the wrappers in heasoftpy/fcn"""
    def run(self):
        super().run()
        fcn = os.path.join('heasoftpy', 'fcn')
        print(f'cleaning wrappers in {fcn}')
        filelist = [f for f in os.listdir(fcn) if '.py' == f[-3:] and not '__' in f]
        for f in filelist:
            file = os.path.join(fcn, f)
            print(f'removing {file}')
            os.remove(file)
        for d in ['build', 'heasoftpy.egg-info', '__pycache__', 'dist', 
                  'heasoftpy-install.log', f'{fcn}/__pycache__']:
            if os.path.exists(d):
                os.system(f'rm -rf {d}')





with open('README.md') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

with open('heasoftpy/version.py') as f:
    lines = f.readlines()
    version = [l for l in lines if '__version__' in l][0].split('=')[1].replace("'", "").strip()

    
setup(
    name='heasoftpy',
    version=version,
    description='Python interface for Heasoft',
    long_description=readme,
    author='HEASARC',
    author_email='a.zoghbi@nasa.gov',
    url='https://heasarc.gsfc.nasa.gov/docs/software/heasoft',
    license=license,
    packages=find_packages(exclude=('tests', 'notebooks')),
    
    cmdclass={
        'build_py': HSPInstallCommand,
        'clean': HSPCleanCommand,
    },
)

