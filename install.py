
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import heasoftpy


# generate python wrappers for all tasks in HEADAS/syspfiles/
heasoftpy.utils.generate_py_code()