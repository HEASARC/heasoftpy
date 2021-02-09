#!/usr/bin/env python3

"""
Installer for the heasoftpy Python interface to the FTools/HTools package.

"""

import collections
#import datetime
import importlib
import inspect
import logging
import os
#import pydoc
import subprocess
import sys
import time

import ape as hsp_ape
import utils

#print(__name__)

#THIS_MODULE = 'heasoftpy' #sys.modules[__name__]

#utils = importlib.import_module('.utils', package='') #THIS_MODULE.__name__)

#utils = importlib.import_module('.utils', package='heasoftpy') #THIS_MODULE.__name__)
#hsp_ape = importlib.import_module('.ape', package='heasoftpy') #THIS_MODULE.__name__)
#hsp_ape = importlib.import_module('.ape', package=THIS_MODULE)
#hsp_tfc = importlib.import_module('.task_file_creator', package=THIS_MODULE.__name__)

__version__ = utils.read_version(os.path.dirname(__file__)).rstrip()

DEBUG = False
#DEBUG = True

LOGFILE_DATETIME = time.strftime('%Y-%m-%d_%H%M%S', time.localtime())
LOG_NAME = ''.join(['heasoftpy_initialization_', LOGFILE_DATETIME, '.log'])
LOG_PATH = os.path.join('/tmp', LOG_NAME)
logging.basicConfig(filename=LOG_PATH,
                    filemode='a', level=logging.INFO)

LOGGER = logging.getLogger('heasoftpy_initialization')
LOG_DT_LST = list(LOGFILE_DATETIME)
LOG_DT_LST.insert(15, ':')
LOG_DT_LST.insert(13, ':')

DBG_MSG = 'Entering heasoftpy module at {}'.\
          format(''.join(LOG_DT_LST).replace('_', ' '))
LOGGER.debug(DBG_MSG)

ENV_PFILES = os.environ['PFILES']
HEADAS_DIR = os.environ['HEADAS']
BIN_DIR = os.path.join(HEADAS_DIR, 'bin')
PERMITTED_MODES = {'a' : 'a', 'A' : 'a', 'auto' : 'a',
                   'h' : 'h', 'H' : 'h', 'hidden' : 'h',
                   'l' : 'l', 'L' : 'l', 'learn' : 'l',
                   'q' : 'q', 'Q' : 'q', 'query' : 'q'}
PERMITTED_TYPES = ['b', 'i', 'r', 's', 'f']

def _get_syspfiles_dir():
    """
    Searches the PFILES environment variable and returns the path for the system
    pfiles directory
    """
#    pfiles_var = os.environ['PFILES']
    pfiles_parts = ENV_PFILES.split(';')        #pfiles_var.split(';')
    if len(pfiles_parts) == 1:
        pfiles_dir = ENV_PFILES
    else:
        pfiles_dir_fnd = False
        for pf_part in pfiles_parts:
            if (pf_part.find('heasoft') != -1) and (pf_part.find('syspfiles') != -1):
                pfiles_dir = pf_part
                pfiles_dir_fnd = True
        if not pfiles_dir_fnd:
            sys.exit('Error! Could not locate syspfiles directory.')
    return pfiles_dir

# Don't want  a one line function, but keeping this code in case more is needed
#def _get_user_pfiles_dir():
#    user_pfiles_dir = os.path.join(os.path.expanduser('~'), 'pfiles')
#    return user_pfiles_dir

SYS_PFILES_DIR = _get_syspfiles_dir()
USER_PFILES_DIR = os.path.join(os.path.expanduser('~'), 'pfiles')
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

def _create_task_file(task_nm, par_name, func_mod_path):
    """
    Creates a file containing the function to run an FTools task (program).
    """
    LOGGER.info('Creating function file: %s', task_nm)
    if DEBUG:
        print('Creating function file:', task_nm)
    task_file_str = ''
    # Create the path to the par file we want
    user_pfile_path = os.path.join(USER_PFILES_DIR, par_name)
    if os.path.exists(user_pfile_path):
        par_path = user_pfile_path
    else:
        par_path = os.path.join(SYS_PFILES_DIR, par_name)
    if os.path.exists(par_path) and os.path.isfile(par_path):
        LOGGER.debug('%s is a good path', par_path)
    else:
        if not os.path.exists(par_path):
            LOGGER.debug('%s was not found', par_path)
        if not os.path.isfile(par_path):
            LOGGER.debug('%s is not a regular file', par_path)
    task_file_str = _create_task_file_header(task_nm)
#    task_file_str += _create_task_help()           # MAY add this at some point
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
    hdr_str += 'import heasoftpy.ape as hsp_ape\n'
    hdr_str += 'import heasoftpy.core.errors as hsp_err\n'
    hdr_str += 'import heasoftpy.core.result as hsp_res\n'
    hdr_str += 'import heasoftpy.utils as hsp_utils\n\n'
    hdr_str += '__version__ = \'{}\'\n\n'.format(__version__)
    return hdr_str

def _create_fn_start(par_path, par_file_dict, task_nm):
    num_req_param = _get_num_req_param(par_file_dict)
    ### Remove after debugging:
#    if task_nm.find('fhelp') != -1:
#        print('for {}, num_req_param = {}'.format(task_nm, num_req_param))
    fn_docstring = _create_function_docstring(task_nm, par_file_dict)
    if num_req_param == 1:
        fn_start_str, indent_lvl = _create_positional_arg_function_start(fn_docstring, par_path,
                                                                         par_file_dict, task_nm)
    else:
        indent_lvl = '    '
        fn_start_str = ''
        fn_start_str += 'def {0}(**kwargs):\n'.format(task_nm)
        fn_start_str += fn_docstring + '\n'
        fn_start_str += ''.join([indent_lvl, 'par_path = \'{}\'\n'.format(par_path)])
        fn_start_str += ''.join([indent_lvl, 'task_params = dict()\n'])

    return fn_start_str, indent_lvl

def _create_positional_arg_function_start(fn_docstring, par_path, param_dict, task_nm):
    indent_lvl = '    '
    fn_start_str = ''
    fn_start_str += 'def {0}(*args, **kwargs):\n'.format(task_nm)
    fn_start_str += fn_docstring + '\n'
    fn_start_str += ''.join([indent_lvl, 'par_path = \'{}\'\n'.format(par_path)])
    fn_start_str += ''.join([indent_lvl, 'task_args = [\'{}\']\n'.format(task_nm)])
    fn_start_str += ''.join([indent_lvl, 'task_params = dict()\n'])
    fn_start_str += ''.join([indent_lvl, 'if len(args) >= 2:\n'])
    fn_start_str += ''.join([indent_lvl,
                             '    err_msg = \'Error! At most one positional argument can be supplied.\'\n'])
    fn_start_str += ''.join([indent_lvl, '    sys.exit(err_msg)\n'])
    fn_start_str += ''.join([indent_lvl, 'elif len(args) == 1:\n'])
    fn_start_str += ''.join([indent_lvl,
                             '    task_args.append(\'{0}={1}\'.format(\'', list(param_dict)[0], '\', args[0]))\n'])
#    fn_start_str += ''.join([indent_lvl, '    task_args.append(\'{0}={1}\'.format(\'infile'\', args[0]))\n'])
    fn_start_str += ''.join([indent_lvl, '    stderr_dest = subprocess.PIPE\n'])
    fn_start_str += ''.join([indent_lvl, 'else:\n'])
    fn_start_str += '\n'
    indent_lvl += indent_lvl
    return fn_start_str, indent_lvl

def _create_task_function(task_nm, par_path):

    # Create body of function (command line creation, subprocess call)
    parfile_dict = hsp_ape.read_par_file(par_path)
    start_str, indent_lvl = _create_fn_start(par_path, parfile_dict, task_nm)
    fn_str = start_str
    fn_str += ''.join([indent_lvl, 'parfile_dict = dict()\n'])
    for param_key in parfile_dict:
        param_key = param_key.strip()
        if param_key == 'prompt':
            # Quotation marks are part of the prompt value, and we don't want to have two sets.
            fn_str += ''.join([indent_lvl,
                               'parfile_dict[\'{0}\'] = {1}\n'.format(param_key, parfile_dict[param_key])])
        else:
            fn_str += ''.join([indent_lvl,
                               'parfile_dict[\'{0}\'] = {1}\n'.format(param_key, parfile_dict[param_key])])
    fn_str += '\n'
    fn_str += ''.join([indent_lvl, 'task_args = [\'{}\']\n'.format(task_nm)])
    fn_str += ''.join([indent_lvl, 'args_ok = True\n'])
    fn_str += ''.join([indent_lvl, 'for kwa in kwargs:\n'])
    fn_str += ''.join([indent_lvl, '    if not kwa == \'stderr\':\n'])
    fn_str += ''.join([indent_lvl, '        if hsp_utils.is_param_ok((kwa, kwargs[kwa]), parfile_dict):\n'])
    fn_str += ''.join([indent_lvl,
                       '            task_args.append(\'{0}={1}\'.format(kwa, kwargs[kwa]))\n'])
    fn_str += ''.join([indent_lvl, '            task_params[kwa] = kwargs[kwa]\n'])
    fn_str += ''.join([indent_lvl, '        else:\n'])
    fn_str += ''.join([indent_lvl, '            args_ok = False\n'])
    fn_str += ''.join([indent_lvl, '            print(\'Error! The {} parameter was not specified correctly. Please correct and try again.\'.format(kwa))\n'])
    fn_str += ''.join([indent_lvl, 'if not args_ok:\n'])
    fn_str += ''.join([indent_lvl, '    return None\n'])
    fn_str += ''.join([indent_lvl, 'params_not_specified = []\n'])
    fn_str += ''.join([indent_lvl, 'for entry in parfile_dict:\n'])
    fn_str += ''.join([indent_lvl, '    if not entry in kwargs:\n'])
    fn_str += ''.join([indent_lvl,
                       '        if hsp_utils.check_query_param(entry, parfile_dict):\n'])
    fn_str += ''.join([indent_lvl, '            params_not_specified.append(entry)\n'])
    fn_str += ''.join([indent_lvl, 'for missing_param in params_not_specified:\n'])
    fn_str += ''.join([indent_lvl,
                       '    param_val = hsp_utils.ask_for_param(missing_param, parfile_dict)\n'])
    fn_str += ''.join([indent_lvl,
                       '    task_args.append(\'{0}={1}\'.format(missing_param, param_val))\n'])
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
    fn_str += '        updated_par_contents = hsp_ape.read_par_file(par_path)\n'
    fn_str += '        par_dict = dict()\n'
    fn_str += '        for parm_key in updated_par_contents:\n'
    fn_str += '            par_dict[parm_key] = updated_par_contents[parm_key][\'default\']\n'
#    fn_str += '\n'
    fn_str += '        task_res.params = par_dict\n'
    fn_str += '    return task_res\n'
    return fn_str

#def _create_task_help():
#    hlp_str = ''
#    hlp_str += 'def help():\n'
#    hlp_str += '    pass\n'
#    return hlp_str

def _get_num_req_param(param_dict):
    """
    Returns the number of required parameters in param_dict.
    """
    req_param = None    # Set to None to serve as an error flag
    if isinstance(param_dict, dict):
        req_param = 0
        for param_key in param_dict:
            if (param_dict[param_key]['mode'] == 'a' or param_dict[param_key]['mode'] == 'q') and param_dict[param_key]['default'] == '':
#            if param_dict[param_key]['mode'] == 'a' and param_dict[param_key]['default'] == '':
                req_param += 1
    return req_param

def _get_task_fhelp(task_nm):
    fhelp_str = 'Sorry, could not find help for {}.'.format(task_nm)
    help_cmd = os.path.join(BIN_DIR, 'fhelp')
    try:
        task_str = ''.join(['task=', task_nm])
        help_proc = subprocess.Popen([help_cmd, task_str], stdin=subprocess.PIPE,
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if task_nm == 'attitude':
            fhelp_out, err = help_proc.communicate(input=b'task\n')
        else:
            fhelp_out, err = help_proc.communicate()
    except:
        err_msg = 'Error finding help for {}.'.format(task_nm)
    try:
        # Convert to string (from a bytes object)
        if not err:
            fhelp_str = fhelp_out.decode()
            fhelp_str = fhelp_str.replace('"""', '').replace('\\x', 'esc-x')
        else:
            fhelp_str = err.decode()
        # With some of the encodings in the help messages, using .startswith
        # was leading to problems.
        #if (fhelp_str[:26] == 'Sorry, could not find help') or \
        #   (err[:17] == 'No help found for'):
        #    fhelp_str = '    No help available via fhelp for {}.'.format(task_nm)
    except TypeError:
        exc_info = sys.exc_info()
        err_msg = 'Type error encountered when attempting to decode help for {}.'.format(task_nm)
        LOGGER.info(err_msg)
        LOGGER.info('type(fhelp_out): %s', type(fhelp_out))
        LOGGER.info('type(fhelp_str): %s', type(fhelp_str))
        LOGGER.info('   type: %s', exc_info[0])
        LOGGER.info('   value: %s', exc_info[1])
        LOGGER.info('   traceback: %s', exc_info[2])
        #LOGGER.info('   te.args: %s', te.args)
    except UnicodeDecodeError:
        exc_info = sys.exc_info()
        err_msg = 'UnicodeDecodeError encountered when attempting to decode help for {}.'.format(task_nm)
        LOGGER.info(err_msg)
        LOGGER.info('type(fhelp_out): %s', type(fhelp_out))
        LOGGER.info('type(fhelp_str): %s', type(fhelp_str))
        LOGGER.info('   type: %s', exc_info[0])
        LOGGER.info('   value: %s', exc_info[1])
        LOGGER.info('   traceback: %s', exc_info[2])
    return fhelp_str

# This has been commented out so that the code does not create a conflict with
# Python's builtin help facility. It is kept here in case it is later decided
# to add this back into the module. It should be noted that help can be obtained
# using fhelp via heasoftpy.fhelp(TASK_NAME)
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
#       print('version: {}'.format(__version__))
#       print('Help for heasoftpy:')

def _import_func_module(task_nm, new_module_path):
    """ Imports a function module pointed to by task_nm and new_module_path. """
    # The following was found at:
    #   https://stackoverflow.com/questions/67631/how-to-import-a-module-given-the-full-path
    # Note: This shouldn't work for Python < 3.5 (including versions of Python 2)
    module_spec = importlib.util.spec_from_file_location(task_nm, new_module_path)
    fn_module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(fn_module)
    return fn_module, module_spec

################################################################################

def main():
    """ Program's primary function """
    print('Entering main()')
    if not os.path.exists(DEFS_DIR):
        os.mkdir(DEFS_DIR)

    par_file_list = os.listdir(SYS_PFILES_DIR)
    num_files = len(par_file_list)
    remaining_files = num_files
    print('Installing {} files. {} files remain.'.format(num_files, remaining_files), end='\r')
    for par_file in par_file_list:
        task_name = os.path.splitext(par_file)[0].replace('-', '_')
        func_module_path = os.path.join(DEFS_DIR, task_name + '.py')
        # if os.path.isfile(func_module_path):
            # (func_module, spec) = _import_func_module(task_name, func_module_path)
            # if '__version__' in func_module.__dict__:
            #     func_mod_ver = utils.ProgramVersion(func_module.__version__)
            #     if func_mod_ver < THIS_MOD_VER:
            #         LOGGER.info('Updating the function %s (%s), which is out-dated.', func_module.__name__, func_module_path)
            #         os.remove(func_module_path)
            #         _create_task_file(task_name, par_file, func_module_path)
        # else:
        _create_task_file(task_name, par_file, func_module_path)
        remaining_files -= 1
        print('Installing {} files. {} files remain.        '.\
              format(num_files, remaining_files), end='\r')

    print('\nInstallation complete!')
    return 0

if __name__ == '__main__':
    sys.exit(main())
