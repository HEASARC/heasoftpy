#!/usr/bin/env python3

"""
Prototyping a function to use a par file to create a function to run a
Heasoft task.

MFC 20190603: added parfile parameters to the docstrings for the defined functions
"""

import collections
import csv
import importlib
import inspect
import logging
import os
import sys

logging.basicConfig(filename='create_function_test.log',
                    filemode='a', level=logging.DEBUG)
LOGGER = logging.getLogger('create_function')
LOGGER.debug('Entering create_function module')

PERMITTED_MODES = {'a' : 'a', 'A' : 'a', 'auto' : 'a',
                   'h' : 'h', 'H' : 'h', 'hidden' : 'h',
                   'l' : 'l', 'L' : 'l', 'learn' : 'l',
                   'q' : 'q', 'Q' : 'q', 'query' : 'q'}
PERMITTED_TYPES = ['b', 'i', 'r', 's', 'f']
PFILES_DIR = os.path.join(os.environ['HEADAS'], 'syspfiles')
HToolsParameter = collections.namedtuple('HToolsParameter', ['name', 'type', \
                                                             'mode', 'default', \
                                                             'min', 'max', \
                                                             'prompt'])
THIS_MODULE = sys.modules[__name__]
THIS_MODULE_DIR = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))


def pdocstring(task):
    """
    Creates a docstring from a HEASoft .par file for a specified task

    :param task: HEASoft task
    returns: array of parameters and descriptions in docstring format
    """
    pdir = os.environ['PFILES'].split(';')[-1]
    task = 'fverify'
    with open(os.path.join(pdir, '{0}.par'.format(task)), 'r') as f:
        ll = f.readlines()

    pdarr = []
    #:param DGDdir: directory containing the downloaded DGD files
    for l in ll:
        p = l.strip().split(',')
        desc = l.strip().split('"')[-2]
        default = ''
        if p[3]:
            default = "(default = {0})".format(p[3])
        pstr = ':param {0}: {1} {2}'.format(p[0], desc, default)
        pdarr.append(pstr)
    return pdarr


def create_function(task_name):
    """ function to create a function (see module docstring for more)
    Including the parameters from the parfile as part of the docstring
    """
    LOGGER.debug('Entering create_function, task_name: %s', task_name)

    function_str = ''
    keyword_pairs = {}
    # Create the path to the par file we want
    pfile_path = os.path.join(PFILES_DIR, task_name + '.par')
    if os.path.exists(pfile_path) and os.path.isfile(pfile_path):
        LOGGER.debug('%s is a good path', pfile_path)
    else:
        LOGGER.debug('%s not found or not a regular file', pfile_path)

    function_str = 'def {0}(**kwargs):\n'.format(task_name)
    # Create body of function (command line creation, subprocess call)
    fn_docstring = '    """ \n '
    fn_docstring += "    Automatically generated function for running the HTools task {0}\n\n".format(task_name)
    pdarr = pdocstring(task_name)
    for par in pdarr:
        fn_docstring += "    {0}\n".format(par)
    fn_docstring += '    """ \n\n'

    function_str += fn_docstring
    function_str += '    import sys\n'
    function_str += '    import subprocess\n'
    function_str += '    args = [\'{}\']\n'.format(task_name)
    function_str += '    for kwa in kwargs:\n'
    function_str += '        args.append(\'{0}={1}\'.format(kwa, kwargs[kwa]))\n'
    function_str += '    task_proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines = True)\n'
    function_str += '    task_out, _ = task_proc.communicate()\n'
    function_str += '    return task_out\n'
    #    function_str += '    '
    LOGGER.debug('At end of create_function(), function_str:\n%s', function_str)
    return function_str


# def create_function(task_name):
#     """ function to create a function (see module docstring for more) """
#     LOGGER.debug('Entering create_function, task_name: %s', task_name)
#
#     function_str = ''
#     keyword_pairs = {}
#     # Create the path to the par file we want
#     pfile_path = os.path.join(PFILES_DIR, task_name + '.par')
#     if os.path.exists(pfile_path) and os.path.isfile(pfile_path):
#         LOGGER.debug('%s is a good path', pfile_path)
#     else:
#         LOGGER.debug('%s not found or not a regular file', pfile_path)
#
#     function_str = 'def {0}(**kwargs):\n'.format(task_name)
#     # Create body of function (command line creation, subprocess call)
#     fn_docstring = '    """ Automatically generated function for running the HTools task {} """\n'.format(task_name)
#     function_str += fn_docstring
#     function_str += '    import sys\n'
#     function_str += '    import subprocess\n'
#     function_str += '    args = [\'{}\']\n'.format(task_name)
#     function_str += '    for kwa in kwargs:\n'
#     function_str += '        args.append(\'{0}={1}\'.format(kwa, kwargs[kwa]))\n'
#     function_str += '    task_proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)\n'
#     function_str += '    task_out, _ = task_proc.communicate()\n'
#     function_str += '    if isinstance(task_out, bytes):\n'
#     function_str += '        task_out = task_out.decode()\n'
#     function_str += '    return task_out\n'
# #    function_str += '    '
#     LOGGER.debug('At end of create_function(), function_str:\n%s', function_str)
#     return function_str

#for task_name in ['ftlist.par', 'ftcopy.par', 'fhelp.par', 'fthelp.par']:
for par_file in os.listdir(PFILES_DIR):
    task_name = os.path.splitext(par_file)[0].replace('-', '_')
    new_module_path = os.path.join(THIS_MODULE_DIR, task_name + '.py')
    if not os.path.exists(os.path.join(THIS_MODULE_DIR, task_name + '.py')):
        func_str = create_function(task_name)
        with open(new_module_path, 'wt') as out_file:
            out_file.write(func_str)

    # The following was found at:
    #https://stackoverflow.com/questions/67631/how-to-import-a-module-given-the-full-path
    # Note that this shouldn't work for Python < 3.5 and 2
    spec = importlib.util.spec_from_file_location(task_name, new_module_path)
    func_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(func_module)
    #func_module = importlib.import_module(task_name)

    setattr(THIS_MODULE, task_name, func_module.__dict__[task_name])

