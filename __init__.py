#!/usr/bin/env python3

"""
Python interface to the FTools/HTools package.

The heasoftpy module provides a Python function corresponding to each
Heasoft/FTools task. Note that dashes ("-") in task names are replaces with
underscores ("_") in the corresponding heasoftpy function.

If there is not already a file containing a function to run a given FTools
program, this will create one upon import. The appropriate parameter file is
used to do this.

Modification history:
Version 0.1 ME:    Initial version
Version 0.1.1 MFC: corrects identification of prompting for required, missing
                   parameters
Version 0.1.2 ME:  Added Error classes and handling errors when the underlying
                   program encounters an error.
Version 0.1.3 ME:  Added checks of function versions and replacement of
                   functions that are outdated.
Version 0.1.4 ME:  Pre-populate the results.params field in a generated function
                   so that all values used by the corresponding FTool are in the
                   params field (which later has user-specified values replace
                   the defaults where appropriate).
Version 0.1.5 ME:  Added help, including putting fhelp contents into the
                   docstrings of the created functions.
Version 0.1.6 ME:  Split creation of functions so that those that can accept
                   a single (positional) argument can do so with that required
                   argument (often the input file) as the default.
Version 0.1.7 ME:  Re-read parameter file after subprocess call to underlying program
                   and load into result.params. Moved _read_par_file function to utils
                   and renamed it read_par_file.

ME = Matt Elliott
MFC = Mike Corcoran
"""

import collections
import datetime
import importlib
import inspect
import logging
import os
import pydoc
import subprocess
import sys
import time

THIS_MODULE = sys.modules[__name__]

#print('THIS_MODULE: {}'.format(THIS_MODULE))

utils = importlib.import_module('.utils', package=THIS_MODULE.__name__)

__version__ = '0.1.6'

LOGFILE_DATETIME = time.strftime('%Y-%m-%d_%H%M%S', time.localtime())
LOG_NAME = ''.join(['heasoftpy_initialization_', LOGFILE_DATETIME, '.log'])
logging.basicConfig(filename=LOG_NAME,
                    filemode='a', level=logging.DEBUG)

LOGGER = logging.getLogger('heasoftpy_initialization')
LOG_DT_LST = list(LOGFILE_DATETIME)
LOG_DT_LST.insert(15, ':')
LOG_DT_LST.insert(13, ':')

DBG_MSG = 'Entering heasoftpy module at {}'.\
          format(''.join(LOG_DT_LST).replace('_', ' '))
LOGGER.debug(DBG_MSG)

HEADAS_DIR = os.environ['HEADAS']
BIN_DIR = os.path.join(HEADAS_DIR, 'bin')
PERMITTED_MODES = {'a' : 'a', 'A' : 'a', 'auto' : 'a',
                   'h' : 'h', 'H' : 'h', 'hidden' : 'h',
                   'l' : 'l', 'L' : 'l', 'learn' : 'l',
                   'q' : 'q', 'Q' : 'q', 'query' : 'q'}
PERMITTED_TYPES = ['b', 'i', 'r', 's', 'f']
PFILES_DIR = os.path.join(HEADAS_DIR, 'syspfiles')

HToolsParameter = collections.namedtuple('HToolsParameter', ['name', 'type', \
                                                             'mode', 'default', \
                                                             'min', 'max', \
                                                             'prompt'])

THIS_MODULE_DIR = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))

DEFS_DIR = os.path.join(THIS_MODULE_DIR, 'defs')

THIS_MOD_VER = utils.ProgramVersion(__version__)

def _create_function_docstring(tsk_nm, par_dict):
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
    docstr_lines.append('\n')
    fhelp_str = _get_task_fhelp(tsk_nm)
    docstr_lines.append(fhelp_str)
    docstr_lines.append('\n')
    docstr_lines.append('    """\n')    # join() doesn't put a \n at the end of the string.
    fn_docstr = '\n'.join(docstr_lines)
    return fn_docstr

# Seems to be deprecated
def _create_function_start(par_file_dict, task_nm):
    fn_start_str = ''
    indent_lvl = '    '
    num_req_param = _get_num_req_param(par_file_dict)
    fn_docstring = _create_function_docstring(task_nm, par_file_dict)

    if num_req_param == 1:
        fn_start_str += 'def {0}(*args, **kwargs):\n'.format(task_nm)
        fn_start_str += fn_docstring + '\n'
        fn_start_str += ''.join([indent_lvl, 'task_args = [\'{}\']\n'.format(task_nm)])
        fn_start_str += ''.join([indent_lvl, 'task_params = dict()\n'])
        fn_start_str += ''.join([indent_lvl, 'if len(args) >= 2:\n'])
        fn_start_str += ''.join([indent_lvl, '    err_msg = \'Error! At most one positional argument can be supplied.\'\n'])
        fn_start_str += ''.join([indent_lvl, '    sys.exit(err_msg)\n'])
        fn_start_str += ''.join([indent_lvl, 'elif len(args) == 1:\n'])
        fn_start_str += ''.join([indent_lvl, '    task_args.append(\'{0}={1}\'.format(\'infile\', args[0]))\n'])
        fn_start_str += ''.join([indent_lvl, '    stderr_dest = subprocess.PIPE\n'])
        fn_start_str += ''.join([indent_lvl, 'else:\n'])
        fn_start_str += '\n'
        indent_lvl += indent_lvl
    else:
        fn_start_str += 'def {0}(**kwargs):\n'.format(task_nm)
        fn_start_str += ''.join([indent_lvl, 'task_params = dict()\n'])
        fn_start_str += fn_docstring + '\n'

    return fn_start_str, indent_lvl


def _create_task_file(task_nm, par_name, func_mod_path):
    """
    Creates a file containing the function to run an FTools task (program).
    """
    LOGGER.debug('Entering _create_task_file, task_nm: %s', task_nm)

    task_file_str = ''
    # Create the path to the par file we want
    par_path = os.path.join(PFILES_DIR, par_name)
    if os.path.exists(par_path) and os.path.isfile(par_path):
        LOGGER.debug('%s is a good path', par_path)
    else:
        if not os.path.exists(par_path):
            LOGGER.debug('%s was not found', par_path)
        if not os.path.isfile(par_path):
            LOGGER.debug('%s is not a regular file', par_path)
    task_file_str = _create_task_file_header(task_nm)
    task_file_str += _create_task_help()
    task_file_str += _create_task_function(task_nm, par_path)
#    task_file_str += '    \n'
    LOGGER.debug('At end of _create_task_file().') #, task_file_str:\n%s', task_file_str)
    with open(func_mod_path, 'wt') as out_file:
        out_file.write(task_file_str)
#    return task_file_str

def _create_task_file_header(task_nm):
    """
    Returns the first few lines of a task function file, including the file docstring, imports,
    and the version.
    """
    hdr_str = '"""\nAutomatically created file containing ' + task_nm + ' function. This is\n'
    hdr_str += 'expected to be imported into (and be part of) the heasoftpy module.\n"""\n\n'
    hdr_str += 'import sys\n'
    hdr_str += 'import subprocess\n'
    hdr_str += 'import heasoftpy.core.errors as hsp_err\n'
    hdr_str += 'import heasoftpy.core.result as hsp_res\n'
    hdr_str += 'import heasoftpy.utils as hsp_utils\n\n'
    hdr_str += '__version__ = \'{}\'\n\n'.format(__version__)
    return hdr_str


def _create_fn_start(par_path, par_file_dict, task_nm):
    fn_start_str = ''
    indent_lvl = '    '
    num_req_param = _get_num_req_param(par_file_dict)
    fn_docstring = _create_function_docstring(task_nm, par_file_dict)

    if num_req_param == 1:
        fn_start_str += 'def {0}(*args, **kwargs):\n'.format(task_nm)
        fn_start_str += fn_docstring + '\n'
        fn_start_str += ''.join([indent_lvl, 'par_path = \'{}\'\n'.format(par_path)])
        fn_start_str += ''.join([indent_lvl, 'task_args = [\'{}\']\n'.format(task_nm)])
        fn_start_str += ''.join([indent_lvl, 'task_params = dict()\n'])
        fn_start_str += ''.join([indent_lvl, 'if len(args) >= 2:\n'])
        fn_start_str += ''.join([indent_lvl, '    err_msg = \'Error! At most one positional argument can be supplied.\'\n'])
        fn_start_str += ''.join([indent_lvl, '    sys.exit(err_msg)\n'])
        fn_start_str += ''.join([indent_lvl, 'elif len(args) == 1:\n'])
        fn_start_str += ''.join([indent_lvl, '    task_args.append(\'{0}={1}\'.format(\'infile\', args[0]))\n'])
        fn_start_str += ''.join([indent_lvl, '    stderr_dest = subprocess.PIPE\n'])
        fn_start_str += ''.join([indent_lvl, 'else:\n'])
        fn_start_str += '\n'
        indent_lvl += indent_lvl
    else:
        fn_start_str += 'def {0}(**kwargs):\n'.format(task_nm)
        fn_start_str += ''.join([indent_lvl, 'par_path = \'{}\'\n'.format(par_path)])
        fn_start_str += ''.join([indent_lvl, 'task_params = dict()\n'])
        fn_start_str += fn_docstring + '\n'

    return fn_start_str, indent_lvl


def _create_task_function(task_nm, par_path):

    # Create body of function (command line creation, subprocess call)
    parfile_dict = utils.read_par_file(par_path)
    start_str, indent_lvl = _create_fn_start(par_path, parfile_dict, task_nm)
    fn_str = start_str
    fn_str += ''.join([indent_lvl, 'parfile_dict = dict()\n'])
    for param_key in parfile_dict:
        param_key = param_key.strip()
        if param_key == 'prompt':
            # Quotation marks are part of the prompt value, and we don't want to have two sets.
            fn_str += ''.join([indent_lvl, 'parfile_dict[\'{0}\'] = {1}\n'.format(param_key, parfile_dict[param_key])])
        else:
            fn_str += ''.join([indent_lvl, 'parfile_dict[\'{0}\'] = {1}\n'.format(param_key, parfile_dict[param_key])])
    fn_str += '\n'
    fn_str += ''.join([indent_lvl, 'task_args = [\'{}\']\n'.format(task_nm)])
    fn_str += ''.join([indent_lvl, 'for kwa in kwargs:\n'])
    fn_str += ''.join([indent_lvl, '    if not kwa == \'stderr\':\n'])
    fn_str += ''.join([indent_lvl, '        task_args.append(\'{0}={1}\'.format(kwa, kwargs[kwa]))\n'])
    fn_str += ''.join([indent_lvl, '        task_params[kwa] = kwargs[kwa]\n'])
    fn_str += ''.join([indent_lvl, 'params_not_specified = []\n'])
    fn_str += ''.join([indent_lvl, 'for entry in parfile_dict:\n'])
    fn_str += ''.join([indent_lvl, '    if not entry in kwargs:\n'])
    fn_str += ''.join([indent_lvl, '        if hsp_utils.check_query_param(entry, parfile_dict):\n'])
    fn_str += ''.join([indent_lvl, '            params_not_specified.append(entry)\n'])
    fn_str += ''.join([indent_lvl, 'for missing_param in params_not_specified:\n'])
    fn_str += ''.join([indent_lvl, '    param_val = hsp_utils.ask_for_param(missing_param, parfile_dict)\n'])
    fn_str += ''.join([indent_lvl, '    task_args.append(\'{0}={1}\'.format(missing_param, param_val))\n'])
    fn_str += ''.join([indent_lvl, '    task_params[missing_param] = param_val\n'])
    fn_str += ''.join([indent_lvl, 'stderr_dest = subprocess.STDOUT\n'])
    fn_str += ''.join([indent_lvl, 'if \'stderr\' in kwargs:\n'])
    fn_str += ''.join([indent_lvl, '    if kwargs[\'stderr\']:\n'])
    fn_str += ''.join([indent_lvl, '        stderr_dest = subprocess.PIPE\n'])

    fn_str += '    task_proc = subprocess.Popen(task_args, stdout=subprocess.PIPE, stderr=stderr_dest)\n'
    fn_str += '    task_out, task_err = task_proc.communicate()\n'
    fn_str += '    if isinstance(task_out, bytes):\n'
    fn_str += '        task_out = task_out.decode()\n'
    fn_str += '    if isinstance(task_err, bytes):\n'
    fn_str += '        task_err = task_err.decode()\n'
    fn_str += '    task_res = hsp_res.Result(task_proc.returncode, task_out, task_err, task_params)\n'
    fn_str += '    if task_res.returncode:\n'
    fn_str += '        raise hsp_err.HeasoftpyExecutionError(task_args[0], task_res)\n'
    fn_str += '    else:\n'
    fn_str += '        updated_par_contents = hsp_utils.read_par_file(par_path)\n'
    fn_str += '        task_res.params = updated_par_contents\n'
    fn_str += '    return task_res\n'
    return fn_str

def _old_create_task_function(task_nm, par_path):
    fn_str = ''
    # Create body of function (command line creation, subprocess call)
    fn_str += 'def {0}(**kwargs):\n'.format(task_nm)
    parfile_dict = hsp_utils.read_par_file(par_path)
    fn_docstring = _create_function_docstring(task_nm, parfile_dict)
    fn_str += fn_docstring + '\n'
    fn_str += '    parfile_dict = dict()\n'
    for param_key in parfile_dict:
        param_key = param_key.strip()
        if param_key == 'prompt':
            # Quotation marks are part of the prompt value, and we don't want to have two sets.
            fn_str += "    parfile_dict[{0}] = {1}\n".format(param_key, parfile_dict[param_key])
        else:
            fn_str += "    parfile_dict['{0}'] = {1}\n".format(param_key, parfile_dict[param_key])
    fn_str += '    args = [\'{}\']\n'.format(task_nm)
    fn_str += '    task_params = dict()\n'
    fn_str += '    for kwa in kwargs:\n'
    fn_str += '        if not kwa == \'stderr\':\n'
    fn_str += '            args.append(\'{0}={1}\'.format(kwa, kwargs[kwa]))\n'
    fn_str += '            task_params[kwa] = kwargs[kwa]\n'
    fn_str += '    params_not_specified = []\n'
    fn_str += '    for entry in parfile_dict:\n'
    fn_str += '        if not entry in kwargs:\n'
    fn_str += '            if hsp_utils.check_query_param(entry, parfile_dict):\n'
    fn_str += '                params_not_specified.append(entry)\n'
    fn_str += '    for missing_param in params_not_specified:\n'
    fn_str += '        param_val = hsp_utils.ask_for_param(missing_param, parfile_dict)\n'
    fn_str += '        args.append(\'{0}={1}\'.format(missing_param, param_val))\n'
    fn_str += '        task_params[missing_param] = param_val\n'
    fn_str += '    stderr_dest = subprocess.STDOUT\n'
    fn_str += '    if \'stderr\' in kwargs:\n'
    fn_str += '        if kwargs[\'stderr\']:\n'
    fn_str += '            stderr_dest = subprocess.PIPE\n'
    fn_str += '    task_proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=stderr_dest)\n'
    fn_str += '    task_out, task_err = task_proc.communicate()\n'
    fn_str += '    if isinstance(task_out, bytes):\n'
    fn_str += '        task_out = task_out.decode()\n'
    fn_str += '    if isinstance(task_err, bytes):\n'
    fn_str += '        task_err = task_err.decode()\n'
    fn_str += '    task_res = hsp_res.Result(task_proc.returncode, task_out, task_err, task_params)\n'
    fn_str += '    if task_res.returncode:\n'
    fn_str += '        raise hsp_err.HeasoftpyExecutionError(args[0], task_res)\n'
    fn_str += '    return task_res\n'
    return fn_str

def _get_num_req_param(param_dict):
    """
    Returns the number of required parameters in param_dict.
    """
    req_param = None    # Set to None to serve as an error flag
    if isinstance(param_dict, dict):
        req_param = 0
        for param_key in param_dict:
            if param_dict[param_key]['mode'] == 'a' and param_dict[param_key]['default'] == '':
                req_param += 1
    return req_param

def _get_task_fhelp(task_nm):
    fhelp_str = 'Sorry, could not find help for {}.'.format(task_nm)
    help_cmd = os.path.join(BIN_DIR, 'fhelp')
    try:
        task_str = ''.join(['task=', task_nm])
        help_proc = subprocess.Popen([help_cmd, task_str], stdout=subprocess.PIPE)
        if task_nm == 'attitude':
            fhelp_out, err = task_proc.communicate(input=b'task\n')
        else:
            fhelp_out, err = help_proc.communicate()
        # Convert to string (from a bytes object)
        fhelp_str = fhelp_out.decode().replace('"""', '').replace('\\x', 'esc-x')
        if fhelps_str.startswith('Sorry, could not find help'):
            fhelp_str = '    No help available via fhelp for {}.'.format(task_nm)
    except:
        err_msg = 'Error finding help for {}.'.format(task_nm)
        print(err_msg)
#        print('\n start of sys.exc_info():')
#        print(sys.exc_info())
#        print('end of sys.exc_info()\n')
    return fhelp_str

def _create_task_help():
    hlp_str = ''
    hlp_str += 'def help():\n'
    hlp_str += '    pass\n'
    return hlp_str


#def help(*args):
#    """
#    Provide a help facility for the module.
#
#    If args is empty, provide the help message for the facility. If args
#   contains the name of a function/task, run fhelp for that task to get the
#   help message to be printed.
#   """
#   #print('in help()')
#   if args:
#       print('help for: {} would be printed here'.format(args[0]))
#       help_str = _get_task_fhelp(args[0])
#       print(help_str)
#   else:
#       print(pydoc.render_doc(__package__))
        #print('version: {}'.format(__version__))
        #print('Help for heasoftpy:')

def _import_func_module(task_nm, new_module_path):
    # The following was found at:
    #   https://stackoverflow.com/questions/67631/how-to-import-a-module-given-the-full-path
    # Note: This shouldn't work for Python < 3.5 (including versions of Python 2)
    spec = importlib.util.spec_from_file_location(task_nm, new_module_path)
    fn_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fn_module)
    return fn_module, spec

################################################################################

if not os.path.exists(DEFS_DIR):
    os.mkdir(DEFS_DIR)

for par_file in os.listdir(PFILES_DIR):
    task_name = os.path.splitext(par_file)[0].replace('-', '_')
    func_module_path = os.path.join(DEFS_DIR, task_name + '.py')

    if os.path.isfile(func_module_path):
#        print('Found {}, checking version'.format(func_module_path))
        (func_module, spec) = _import_func_module(task_name, func_module_path)
        if '__version__' in func_module.__dict__:
            func_mod_ver = utils.ProgramVersion(func_module.__version__)
            if func_mod_ver < THIS_MOD_VER:
                print('Updating the function {0} ({1}), which is out-dated.'.format(func_module.__name__, func_module_path))
                os.remove(func_module_path)
                _create_task_file(task_name, par_file, func_module_path)
    else:
        _create_task_file(task_name, par_file, func_module_path)
        (func_module, spec) = _import_func_module(task_name, func_module_path)

    setattr(THIS_MODULE, task_name, func_module.__dict__[task_name])
