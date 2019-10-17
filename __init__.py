#!/usr/bin/env python3

"""
Creates a Python interface to the FTools/HTools package.

If there is not already a file containing a function to run a given FTools program,
this will create one upon import. It uses the appropriate paramter file to do this.

Version 0.1 ME: initial version
Version 0.1.1 MFC: corrects identification of prompting for required, missing parameters
Version 0.1.2 ME: Added Error classes and handling errors when the underlying program
                  encounters an error.

ME = Matt Elliott
MFC = Mike Corcoran
"""

import collections
import csv
import datetime
import importlib
import inspect
import logging
import os
import sys
import time

__version__ = '0.1.2'

logfile_datetime = time.strftime('%Y-%m-%d_%H%M%S', time.localtime())
LOG_NAME = ''.join(['heasoftpy_initialization_', logfile_datetime, '.log'])
logging.basicConfig(filename=LOG_NAME,
                    filemode='a', level=logging.DEBUG)
LOGGER = logging.getLogger('heasoftpy_initialization')
log_dt_lst = list(logfile_datetime)
log_dt_lst.insert(15, ':')
log_dt_lst.insert(13, ':')

dbg_msg = 'Entering heasoftpy module at {}'.\
          format(''.join(log_dt_lst).replace('_', ' '))
LOGGER.debug(dbg_msg)

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

DEFS_DIR = os.path.join(THIS_MODULE_DIR, 'defs')

def _make_function_docstring(tsk_nm, par_dict):
    """
    Create a string (expected to be used as the docstring for an automagically
    created function) listing the parameters of the function named in tsk_nm,
    and as contained in par_dict.
    """
    docstr_lines = list()
    docstr_lines.append('    """')
    docstr_lines.append('    Automatically generated function for the HTools task {}.'.\
                        format(tsk_nm))
    docstr_lines.append('')
    for param_key in par_dict.keys():
        docstr_lines.append('    :param {0}: {1} (default = "{2}")'.\
                            format(param_key, par_dict[param_key]['prompt'],
                                   par_dict[param_key]['default']))
    docstr_lines.append('    """\n')    # join() doesn't put a \n at the end of the string.
    fn_docstr = '\n'.join(docstr_lines)
    return fn_docstr

def _read_par_file(par_path):
    """
    Reads a par file, returning the contents as a dictionary with the parameter
    names as keys.
    """
    par_contents = dict()     # list()
    try:
        with open(par_path, 'rt') as par_hndl:
            par_reader = csv.reader(par_hndl, delimiter=',', quotechar='"', \
                                    quoting=csv.QUOTE_ALL, \
                                    skipinitialspace=True)
            for param in par_reader:
                if len(param) > 1 and not param[0].strip().startswith('#'):
                    param_dict = dict()
                    try:
                        param_dict = {'type':     param[1], 'mode':     param[2],
                                      'default':  param[3].strip(),
                                      'min':      param[4], 'max':      param[5],
                                      'prompt':   param[6]}
                    except IndexError:
                        print('Error processing {}.'.format(par_path))

                    par_contents[param[0].strip()] = param_dict
    except FileNotFoundError:
        err_msg = 'Error! Par file {} could not be found.'.format(par_path)
        sys.exit(err_msg)
    except PermissionError:
        err_msg = 'Error! A permission error was encountered reading {}.'.format(par_path)
        sys.exit(err_msg)
    except IsADirectoryError:
        err_msg = 'Error! {} is a directory, not a file.'.format(par_path)
        sys.exit(err_msg)

    return par_contents

def _create_function(task_nm, par_name):
    """ function to create a function (see module docstring for more) """
    LOGGER.debug('Entering _create_function, task_nm: %s', task_nm)

    function_str = ''
    # Create the path to the par file we want
    par_path = os.path.join(PFILES_DIR, par_name)
    if os.path.exists(par_path) and os.path.isfile(par_path):
        LOGGER.debug('%s is a good path', par_path)
    else:
        if not os.path.exists(par_path):
            LOGGER.debug('%s was not found', par_path)
        if not os.path.isfile(par_path):
            LOGGER.debug('%s is not a regular file', par_path)

    function_str = '"""\nAutomatically created file containing ' + task_nm + ' function. This is\n'
    function_str += 'expected to be imported into (and be part of) the heasoftpy module.\n"""\n\n'
    function_str += 'import heasoftpy.errors as hsp_err\n'
    function_str += 'import sys\n'
    function_str += 'import subprocess\n'
    function_str += 'import heasoftpy.result as hsp_res\n'
    function_str += 'import heasoftpy.utils as hsp_utils\n\n'
    function_str += 'def {0}(**kwargs):\n'.format(task_nm)
    # Create body of function (command line creation, subprocess call)
    parfile_dict = _read_par_file(par_path)
    fn_docstring = _make_function_docstring(task_nm, parfile_dict)
    function_str += fn_docstring + '\n'
    function_str += '    parfile_dict = dict()\n'
    for param_key in parfile_dict:
        param_key = param_key.strip()
        if param_key == 'prompt':
            # Quotation marks are part of the prompt value, and we don't want to have two sets.
            function_str += "    parfile_dict[{0}] = {1}\n".format(param_key, parfile_dict[param_key])
        else:
            function_str += "    parfile_dict['{0}'] = {1}\n".format(param_key, parfile_dict[param_key])
    function_str += '    args = [\'{}\']\n'.format(task_nm)
    function_str += '    task_params = dict()\n'
    function_str += '    for kwa in kwargs:\n'
    function_str += '        if not kwa == \'stderr\':\n'
    function_str += '            args.append(\'{0}={1}\'.format(kwa, kwargs[kwa]))\n'
    function_str += '            task_params[kwa] = kwargs[kwa]\n'
    function_str += '    params_not_specified = []\n'
    function_str += '    for entry in parfile_dict:\n'
    function_str += '        if not entry in kwargs:\n'
    function_str += '            if hsp_utils.check_query_param(entry, parfile_dict):\n'
    function_str += '                params_not_specified.append(entry)\n'
    function_str += '    for missing_param in params_not_specified:\n'
    function_str += '        param_val = hsp_utils.ask_for_param(missing_param, parfile_dict)\n'
    function_str += '        args.append(\'{0}={1}\'.format(missing_param, param_val))\n'
    function_str += '        task_params[missing_param] = param_val\n'
    function_str += '    stderr_dest = subprocess.STDOUT\n'
    function_str += '    if \'stderr\' in kwargs:\n'
    function_str += '        if kwargs[\'stderr\']:\n'
    function_str += '            stderr_dest = subprocess.PIPE\n'
    function_str += '    task_proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=stderr_dest)\n'
    function_str += '    task_out, task_err = task_proc.communicate()\n'
    function_str += '    if isinstance(task_out, bytes):\n'
    function_str += '        task_out = task_out.decode()\n'
    function_str += '    if isinstance(task_err, bytes):\n'
    function_str += '        task_err = task_err.decode()\n'
    function_str += '    task_res = hsp_res.Result(task_proc.returncode, task_out, task_err, task_params)\n'
    function_str += '    if task_res.returncode:\n'
    function_str += '        raise hsp_err.HeasoftpyExecutionError(args[0], task_res)\n'
    function_str += '    return task_res\n'
#    function_str += '    \n'
    LOGGER.debug('At end of _create_function(), function_str:\n%s', function_str)
    return function_str

if not os.path.exists(DEFS_DIR):
    os.mkdir(DEFS_DIR)

for par_file in os.listdir(PFILES_DIR):
    task_name = os.path.splitext(par_file)[0].replace('-', '_')
    new_module_path = os.path.join(DEFS_DIR, task_name + '.py')

    #if not os.path.exists(os.path.join(THIS_MODULE_DIR, task_name + '.py')):
    if not os.path.isfile(new_module_path):
        func_str = _create_function(task_name, par_file)
        with open(new_module_path, 'wt') as out_file:
            out_file.write(func_str)

    # The following was found at:
    #   https://stackoverflow.com/questions/67631/how-to-import-a-module-given-the-full-path
    # Note that this shouldn't work for Python < 3.5 and 2
    spec = importlib.util.spec_from_file_location(task_name, new_module_path)
    func_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(func_module)

    setattr(THIS_MODULE, task_name, func_module.__dict__[task_name])
#2345678901234567890123456789012345678901234567890123456789012345678901234567890
