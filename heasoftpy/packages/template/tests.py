# put in the same place at the package __init__.py
# i.e in package/{name}/
import unittest
import os
import importlib

os.environ['__INSTALLING_HSP'] = 'yes'
from heasoftpy.core import HSPTask


# find out where __init__ for the package it #
current_dir = os.path.dirname(__file__)
init = os.path.join(current_dir, '__init__.py')

# if no __init__.py file, fail
if not os.path.exists(init):
    raise ValueError('Unable to find an __init__.py file in the package')


# read __init__; __all__ should contain a list of method/classes in this package
with open(init) as fp: exec(fp.read())
try:
    __all__
except NameError:
    raise ValueError('__all__ was not defined in __init__.py')

# if empty __all__, fail
if len(__all__) == 0:
    raise ValueError('__all__ does not define any classes or methods')
    
    
# divide the content of __all__ into methods and classes
classes, methods = [], []
for _a in __all__:
    _a = eval(_a)
    if isinstance(_a, type):
        classes.append(_a)
    else:
        methods.append(_a)


class TestPyTasks(unittest.TestCase):
    """Do basic tests for the package structure"""
    
    def check_par_files(self):
        self.assertEqual(1, 1)
    
    
        
if __name__ == '__main__':
    unittest.main()
