#!/usr/bin/env python3

"""
Creates a Python interface to the FTools/HTools package.

If there is not already a file containing a function to run a given FTools program, this will create one upon import. It uses the appropriate paramter file to do this.
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

#2345678901234567890123456789012345678901234567890123456789012345678901234567890

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

def _ask_for_param(p_name, p_dict):
    if p_dict['prompt']:
        query_msg = 'No value found for {0}.\n{1}'.format(p_name, p_dict['prompt'])
    else:
        query_msg = 'No value found for {0}.\n{1}'.format(p_name, p_dict['prompt'])
    usr_inp = ''
    while not usr_inp:
        try:
            usr_inp = input(query_msg)
        except EOFError:
            sys.exit('\nKeyboard interrupt received, program stopping.')

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

#def read_par_file(par_path, verbose=False):
#    """
#    Creates a docstring from a HEASoft .par file for a specified task
#
#    :param task: HEASoft task
#    returns: array of parameters and descriptions in docstring format
#    """
#    param_dict = dict()
#    skipit = False
#    parfile = par_path #os.path.join(PFILES_DIR, '{0}.par'.format(task))
#    pdarr = []
#    try:
#        with open(parfile, 'r') as par_hndl:
#            ll = par_hndl.readlines()
#    except Exception as errmsg:
#        skipit = True
#        print('Problem reading {0} ({1})'.format(parfile, errmsg))
#        print('exception parts:')
#        for ep in sys.exc_info():
#            print('   {}'.format(ep))
#    if not skipit:
#        for l in ll:
#            skipit = False
#            if l.strip().startswith('#'):
#                skipit = True
#            p = l.strip().split(',')
#            pstr = ''
#            try:
#                desc = l.strip().split('"')[-2]
#            except Exception as errmsg:
#                skipit = True
#                if verbose:
#                    print('Problem parsing parameter file for {0}'.format(task))
#            if not skipit:
#                default = ''
#                try:
#                    if p[3]:
#                        default = "(default = {0})".format(p[3])
#                except Exception:
#                    pass
#                pstr = ':param {0}: {1} {2}'.format(p[0], desc, default)
#                min_val = None
#                max_val = None
#                prompt = None
#                if len(p) > 4:
#                    try:
#                        min_val = float(p[4])
#                    except ValueError:
#                        pass
#                    try:
#                        max_val = float(p[5])
#                    except ValueError:
#                        pass
#                param_dict[p[0]] = {'type': p[1], 'mode': p[2], 'default': p[3],
#                                    'min': min_val, 'max': max_val,
#                                    'prompt': p[6]}
#            pdarr.append(pstr)
#    return pdarr, param_dict
#


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
    #keyword_pairs = {}
    # Create the path to the par file we want
    par_path = os.path.join(PFILES_DIR, par_name)
    if os.path.exists(par_path) and os.path.isfile(par_path):
        LOGGER.debug('%s is a good path', par_path)
    else:
        if not os.path.exists(par_path):
            LOGGER.debug('%s was not found', par_path)
        if not os.path.isfile(par_path):
            LOGGER.debug('%s is not a regular file', par_path)

    function_str = '"""\n'
    function_str += 'Automatically created file containing ' + task_nm + '\n'
    function_str += 'function. This is expected to be imported into (and be\n'
    function_str += 'part of) the heasoftpy module.\n'
    function_str += '"""\n\n'
    function_str += 'import sys\n'
    function_str += 'import subprocess\n'
    function_str += 'import heasoftpy.result as hsp_res\n\n'
    function_str += 'def {0}(**kwargs):\n'.format(task_nm)
    # Create body of function (command line creation, subprocess call)
    param_dict = _read_par_file(par_path)
    fn_docstring = _make_function_docstring(task_nm, param_dict)
    function_str += fn_docstring
    function_str += '    param_dict = dict()\n'
    for param_key in param_dict.keys():
        param_key = param_key.strip()
        if param_key == 'prompt':
            # Quotation marks are part of the prompt value, and we don't want to have two sets.
            function_str += "    param_dict[{0}] = {1}\n".format(param_key, param_dict[param_key])
        else:
            function_str += "    param_dict['{0}'] = {1}\n".format(param_key, param_dict[param_key])
    function_str += '    args = [\'{}\']\n'.format(task_nm)
    function_str += '    for kwa in kwargs:\n'
    function_str += '        if not kwa == \'stderr\':\n'
    function_str += '            args.append(\'{0}={1}\'.format(kwa, kwargs[kwa]))\n'
    function_str += '    params_not_specified = []\n'
    function_str += '    for param in param_dict:\n'
    function_str += '        if not param in kwargs:\n'
    function_str += '            if param_dict[param][\'mode\'].find(\'h\') == -1:\n'
    function_str += '                params_not_specified.append(param)\n'
    function_str += '    for missing_param in params_not_specified:\n'
    function_str += '        param_val = heasoftpy._ask_for_param(missing_param, param_dict)\n'
    function_str += '        args.append(\'{0}={1}\'.format(missing_param, param_val))\n'

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
    function_str += '    task_res = hsp_res.Result(task_proc.returncode, task_out, task_err)\n'
    function_str += '    return task_res\n'
#    function_str += '    \n'
    LOGGER.debug('At end of _create_function(), function_str:\n%s', function_str)
    return function_str

if not os.path.exists(DEFS_DIR):
    os.mkdir(DEFS_DIR)

#for task_name in ['ftlist.par', 'ftcopy.par', 'fhelp.par', 'fthelp.par']:
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
    #func_module = importlib.import_module(task_name)

#    setattr(THIS_MODULE, task_name, func_module.__dict__[task_name])
    setattr(THIS_MODULE, task_name, func_module.__dict__[task_name])
#2345678901234567890123456789012345678901234567890123456789012345678901234567890
