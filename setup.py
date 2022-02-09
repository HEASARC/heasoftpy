
from setuptools import setup, find_packages
from setuptools.command.install import install
from setuptools.command.build_py import build_py
from distutils.command.clean import clean
from setuptools.command.test import test
import os
import sys
import glob


class HSPInstallCommand(build_py):
    """Run install.py before doing the standard install"""
    def run(self):
        # add current dir to path to import (or call) install.py
        # install.py will fail is HEADAS is not initialized
        sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
        import install as hspinstall
        hspinstall._do_install()
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
        cwd = os.getcwd()
        for d in ['build', 'heasoftpy.egg-info', '__pycache__', 'dist', 
                  'heasoftpy-install.log', f'{fcn}/__pycache__', '.pytest_cache',
                 '.eggs', '*.pyc', '.ipynb_checkpoints']:
            #[os.remove(x) for x in glob.iglob(os.path.join(cwd, "**", d), recursive=True)]
            for f in glob.iglob(os.path.join(cwd, "**", d), recursive=True):
                if os.path.exists(f):
                    os.system(f'rm -rf {f}')

def build_requirements():
    """Build a list of requirements from the main and sub-packages"""
    # requirements from the core of heasoftpy.
    with open('requirements.txt') as fp:
        requirements = fp.readlines()
    requirements = [r.strip() for r in requirements 
                    if not r.startswith('#') or len(r) == 0]
    
    # requirements from sub-packages
    sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
    import install as hspinstall
    packages = hspinstall._find_py_packages()
    for package in packages:
        tasks, reqs = hspinstall._read_package_setup(package)
        for r in reqs:
            if not r in requirements:
                requirements.append(r)
    return requirements



class HSPTestCommand(test):
    def run(self):
        self.distribution.install_requires = []
        super().run()
        

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
    python_requires=">=3.6",
    install_requires=build_requirements(),
    
    cmdclass={
        'build_py': HSPInstallCommand,
        'clean': HSPCleanCommand,
        'test': HSPTestCommand,
    },
    setup_requires=['pytest-runner'],
    tests_require=['pytest'],
)

