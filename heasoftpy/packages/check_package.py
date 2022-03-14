#/usr/bin/env python
"""
A script to check that a package under heasoftpy/packages/ is consistent
with expectation.

Call from inisde the package of interest. For example, for the package template,
this should called from packages/template with a call like:
>> python ../check_package.py

"""

import os
import sys
import importlib

# make sure we can access current verions of heasoftpy
# assume called from: heasoftpy/packages/package_name
CURRENT_DIR = os.getcwd()
sys.path.insert(0, os.path.abspath(os.path.join(CURRENT_DIR, '../../..')))

# we don't want to load all packages
os.environ['__INSTALLING_HSP'] = 'yes'
from heasoftpy.core import HSPTask


def check_package():

    # what is the name of the package
    cwd = os.getcwd()
    package = os.path.split(cwd)[-1]

    # check required files are present
    required_files = ['__init__.py', 'setup.py']
    for file in required_files:
        if not os.path.exists(file):
            raise ValueError(f'Unable to find an file {file} in the package')


    # read __init__; __all__ should contain a list of method/classes in this package
    with open('__init__.py', 'r') as fp:
        _read = False
        _comment = False
        _all = []
        for line in fp.readlines():
            if not _comment and '"""' in line:
                _comment = True
            elif _comment and '"""' in line:
                _comment = False
            
            if not _comment and '__all__' in line and not line.startswith('#'):
                _read = True
                #_all.append(line)
            if _read and ']' in line:
                _all.append(line)
                _read = False
            if _read:
                _all.append(line)
    if len(_all) == 0:
        raise ValueError(f'__init__.py does not appear to define a variable __all__')
    _all = eval(''.join(_all).split('=')[1])
    if len(_all) == 0:
        raise ValueError(f'__all__ is empty in __init__.py')
    
    
        
if __name__ == '__main__':
    check_package()
