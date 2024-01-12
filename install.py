
import sys
import os
import logging
import glob
import importlib
import shutil
import subprocess
from setuptools.command.build_py import build_py


# Where to install the pure-python executable and parameter file #
if not 'HEADAS' in os.environ:
    raise RuntimeError('heasoft needs to be initialized before running this script')

# packages that use heasoftpy
# Typically, this means they have their code under
# $HEADAS/../{mission}/x86../lib/python/heasoftpy/{subpackage}
SUBPACKAGES = ['nicer', 'ixpe']


## --- setup logger --- ##
logger = logging.getLogger('heasoftpy-install')
logger.setLevel(logging.DEBUG)

# log to screen
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# create formatter and add it to the handlers
tformat = '%Y-%m-%d %H:%M:%S'
formatter = logging.Formatter('%(asctime)s - %(levelname)5s - %(message)s', tformat)
ch.setFormatter(formatter)

# add the handlers to the logger
logger.addHandler(ch)
## -------------------- ##


class HSPInstallCommand(build_py):
    """Run install.py to generate the wrappers before doing the standard install
    This is triggered by tool.setuptools.cmdclass in pyproject.toml
    """
    def run(self):
        _do_install()
        super().run()


def _do_install():
    logger.info('-'*60)
    logger.info('Starting heasoftpy installation ...')

    # python wrappers for heasoft-native tools
    _create_py_wrappers()

    # add subpackages
    _add_sub_packages()

## ---------------------------------- ##
## python wrappers for built-in tools ##
def _create_py_wrappers():

    # the following prevents sub-package from being imported
    # as they may depend on the functions in heasoftpy,that we will install here.
    os.environ['__INSTALLING_HSP'] = 'yes'

    # add heasoftpy location to sys.path as it is not installed yet
    current_dir = os.path.abspath(os.path.dirname(__file__))
    sys.path.insert(0, current_dir)
    from heasoftpy.utils import generate_py_code


    logger.info('-'*30)
    logger.info('Creating python wrappers ...')
    try:
        list_of_files = generate_py_code()
        # add the generated files to heasoftpy.egg-info so they are 
        # installed correctly
        with open(f'heasoftpy.egg-info/SOURCES.txt', 'a') as fp:
            fp.write('\n' + ('\n'.join(list_of_files)))
    except:
        logger.error('Failed in generating python wrappers')
        raise
    logger.info('Python wrappers created sucessfully!')
    logger.info('-'*30)

    # remove the __INSTALLING_HSP variable we added at the start
    del os.environ['__INSTALLING_HSP']
## ---------------------------------- ##

## ---------------------------------- ##
## python wrappers for built-in tools ##
def _add_sub_packages():
    """Find and install subpackages from other places in heasoft"""
    if not 'HEADAS' in os.environ:
        msg = 'HEADAS not defined. Please initialize Heasoft!'
        logger.error(msg)
        raise ValueError(msg)

    # find installation folder name
    headas = os.environ['HEADAS']
    inst_dir = os.path.basename(headas)

    # loop through subpackages
    logger.info('-'*30)
    logger.info('Looking for subpackages ...')
    for subpackage in SUBPACKAGES:
        pth = f"{headas}/../{subpackage}/{inst_dir}/lib/python/heasoftpy/{subpackage}"
        if os.path.exists(pth):
            logger.info(f'Found {subpackage} ...')
            os.system(f'cp -r {pth} heasoftpy/')
        else:
            logger.info(f'No {subpackage} subpackage, skipping ...')


    
if __name__ == '__main__':
    help_txt = """This script is not meant to run directly.
Please use: pip install .

Then, copy build/lib/heasoftpy to a location where python can find it,
or add build/lib to your PYTHONPATH.
"""
    print(help_txt)