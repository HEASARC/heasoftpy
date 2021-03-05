#!/usr/bin/env python3

"""
Python interface to the FTools/HTools package.

The heasoftpy module provides a Python function corresponding to each
Heasoft/FTools task. Note that dashes ("-") in task names are replaces with
underscores ("_") in the corresponding heasoftpy function.

See the update_history file for the module's modification history.
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

utils = importlib.import_module('.utils', package=THIS_MODULE.__name__)
hsp_ape = importlib.import_module('.ape', package=THIS_MODULE.__name__)

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
#        pfiles_dir = pfiles_var
        pfiles_dir = ENV_PFILES
    else:
        pfiles_dir_fnd = False
        sys_pfiles_parts = pfiles_parts[1].split(':')
        for pf_part in sys_pfiles_parts:
            if pf_part.find('syspfiles') != -1:
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

def _create_local_pfiles_dir(pfiles_dir, orig_pfiles):
    try:
        os.mkdir(pfiles_dir)
        os.environ['PFILES'] = ';'.join([pfiles_dir, orig_pfiles])
    except OSError:
        err_msg = 'Error! Could not create directory {0}. PFILES remains set to {1}'.\
                  format(pfiles_dir, orig_pfiles)
        print(err_msg)

#2345678901234567890123456789012345678901234567890123456789012345678901234567890

def local_pfiles(pfiles_dir=None):
    """
    Resets the PFILES environment variable, useful for "batch mode processing"
    in which the software may run several times simultaneously (thus over-
    writing one another's parameter files). If the pfiles_dir parameter holds a
    value, the PFILES environment variable will be set to that value prepended
    $HEADAS/syspfiles. If pfiles_dir does not hold a value, the PFILES
    environment variable will be prepended with /tmp/PID.tmp (where PID is
    the process identifier for the current instantiation of the module).

    More details about using HEASoft in batch processing can be found at:
    https://heasarc.gsfc.nasa.gov/lheasoft/scripting.html
    """

    pfiles_env = None
    sys_pfiles = os.path.join(os.environ['HEADAS'], 'syspfiles')
    if pfiles_dir:
#        print('Received {} as a user specified pfile setting, but that functionality is not yet implemented'.format(pfiles_dir))
        if os.path.exists(pfiles_dir):
            if not os.path.isdir(pfiles_dir):
                print('{0} exists, but is not a directory. PFILES remains set to {1}.'.\
                      format(pfiles_dir, os.environ['PFILES']))
            else:
                pfiles_env = ';'.join([pfiles_dir, sys_pfiles])
                os.environ['PFILES'] = pfiles_env
        else:
            _create_local_pfiles_dir(pfiles_dir, sys_pfiles)
            pfiles_env = ';'.join([pfiles_dir, sys_pfiles])
            os.environ['PFILES'] = ';'.join([pfiles_dir, sys_pfiles])
#            print('The directory {0} does not exist. PFILES remains set to {1}.'.\
#                  format(pfiles_dir, orig_pfiles))
    else:
        pid_str = str(os.getpid())
        pfiles_tmp_path = os.path.join('/tmp', pid_str + '.tmp')
        print('PID based tmp pfile directory: {}'.format(pfiles_tmp_path))
        _create_local_pfiles_dir(pfiles_tmp_path, sys_pfiles)
        pfiles_env = ';'.join([pfiles_tmp_path, sys_pfiles])
        os.environ['PFILES'] = pfiles_env
    return pfiles_env

################################################################################

if not os.path.exists(DEFS_DIR):
    os.mkdir(DEFS_DIR)

par_file_list = os.listdir(SYS_PFILES_DIR)
for par_file in par_file_list:
    task_name = os.path.splitext(par_file)[0].replace('-', '_')
    func_module_path = os.path.join(DEFS_DIR, task_name + '.py')
    if os.path.isfile(func_module_path):
        (func_module, spec) = _import_func_module(task_name, func_module_path)
        setattr(THIS_MODULE, task_name, func_module.__dict__[task_name])
    else:
        print('Module {} not found.'.format(task_name))
print()
