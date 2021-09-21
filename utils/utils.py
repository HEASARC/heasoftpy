"""
Utilities for the heasoftpy module, generally intended for use by the module,
not called by users.
"""

import csv
import os
import subprocess
import sys

from ..core import result as hsp_res
from ..par_reader import read_par_file, type_switch

def ask_for_param(p_name, p_dict):
    """
    Asks user for parameter named in p_name.

    :param p_name: parameter name
    :param p_dict: parameter dictionary for function
    :return: The user input
    """
    if 'prompt' in p_dict[p_name]:
        query_msg = ''.join([p_dict[p_name]['prompt'], ' (default=',
                             str(p_dict[p_name]['default']), ') > '])
    else:
        query_msg = 'No value found for {0}.\nPlease enter: '.format(p_name+' > ')
    usr_inp = ''
    while not str(usr_inp):
        try:
            usr_inp = input(query_msg)
            if usr_inp == '':
                usr_inp = p_dict[p_name]['default']
            else:
                p_dict[p_name]['default'] = usr_inp
                try:
                    usr_inp = type_switch(p_dict[p_name]['type'])(str(usr_inp).strip())
                except ValueError:
                    print(f'ValueError encountered converting "{usr_inp}" to int')
        except EOFError:
            sys.exit('\nKeyboard interrupt received, program stopping.')
    return usr_inp

def check_query_param(p_name, p_dict):
    """
    checks whether a user should be queried for a parameter value if parameter not specified
    see https://heasarc.gsfc.nasa.gov/docs/software/lheasoft/headas/pil/node12.html

    :param p_name: parameter name
    :param p_dict: parameter dictionary for function
    :return: True if user needs to be queried for parameter value, False if not
    """
    ans = False
    if 'a' in p_dict[p_name]['mode']:
        if 'q' in p_dict['mode']['default']:
            ans = True
    if 'q' in p_dict[p_name]['mode']:
        ans = True
    return ans

def is_param_ok(param, par_dict):
    """
    Returns True when the parameter passed in via param is verified to comply with
    the rules in par_dict. False is returned otherwise.

    Function parameters:
    param - a 2 item tuple containing indicating the parameter's name and value.
    par_dict - the parameter rules dictionary against which param should be checked
    """
    param_ok = False
    if param[0] in par_dict:
        param_type = par_dict[param[0]]['type']
        if param_type == 's':
            # Is the following redundant? Everything will be a string when it "arrives"  ...
            if isinstance(param[1], str):
                param_ok = True
        elif param_type == 'i':
            try:
                _ = int(param[1])
                param_ok = True
            except ValueError:
                #pass
                print('ValueError encountered converting "{}" to int'.format(param[1]))
        elif param_type == 'b':
            if isinstance(param[1], str):
                param_lower = param[1].lower()
                if param_lower in ['y', 'yes', 'n', 'no']:
                    param_ok = True
            # To do: Figure what what is acceptable here. They seem to want "y", "n", "t", "f",
            # "1", "0", etc. to be acceptable ...
        elif param_type == 'r':
            try:
                _ = float(param[1])
                param_ok = True
            except ValueError:
                print('ValueError encountered converting "{}" to float'.format(param[1]))
        elif param_type.find('f') != -1:
            ### For now, checking for str. To do: find out what needs to be do for a "file type"
            if isinstance(param[1], str):
                param_ok = True
    else:
        print('Error! Invalid parameter type {}'.format(param[0]))
    return param_ok

def get_pfile(exename,user=False):
    """Get the path to the pfile.

    user=False means return user's dir not system even if it doesn't exist."""
    if 'HEADAS' in os.environ:
        sys_par_path = os.path.join(
            os.environ['HEADAS'],
            'syspfiles',
            ''.join([str(exename), '.par']))
    else:
        sys.exit('Error! HEADAS not in the environment. \
        Have you run the init script?')
    pfiles = os.environ['PFILES'].split(';')

    if len(pfiles) > 1 and not user:
        loc_par_path = os.path.join(pfiles[0], ''.join([str(exename), '.par']))
    if os.path.exists(loc_par_path):
        par_path = loc_par_path
    elif user:
        par_path=loc_par_path
    else:
        par_path = sys_par_path
    return par_path

def runit(exename, params_list, task_params, stderr_dest, par_path):
    """Call a task;  the guts of the non-Python tool wrapper.  DOESN'T WORK!!!

    Haven't figured out what's needed for args.  Some of this is in the params class.
    Finish this later.

    Well, it works now. It's kludged, doesn't use the params class, and needs
    other improvements, but does run in experimental code.
    
    """
    task_args = [ exename ] + params_list
    task_proc = subprocess.Popen(task_args, stdout=subprocess.PIPE, stderr=stderr_dest)
    task_out, task_err = task_proc.communicate()
    if isinstance(task_out, bytes):
        task_out = task_out.decode()
    if isinstance(task_err, bytes):
        task_err = task_err.decode()
    task_res = hsp_res.Result(task_proc.returncode, task_out, task_err, task_params)
    if task_res.returncode:
        raise hsp_err.HeasoftpyExecutionError(task_args[0], task_res)
    updated_par_contents = read_par_file(par_path)
    par_dict = dict()
    for parm_key in updated_par_contents:
        par_dict[parm_key] = updated_par_contents[parm_key]['default']
    task_res.params = par_dict
    return task_res


def do_not_call_this_archived_code():
# def runit(exename, pars):
# Stuff from runit that isn't in use right now
    task_args = ['fdump']
    task_params = dict(pars)
    stderr_dest = subprocess.STDOUT
    if len(args) >= 2:
        err_msg = 'Error! At most one positional argument can be supplied.'
        sys.exit(err_msg)
    elif len(args) == 1:
        if isinstance(args[0], dict):
            if 'infile' in args[0]:
                stderr_dest = subprocess.PIPE
    else:
        if pars['stderr']:
            stderr_dest = subprocess.PIPE

# The code below has been put into runit; kept for reference/to have "original"
    task_proc = subprocess.Popen(task_args, stdout=subprocess.PIPE, stderr=stderr_dest)
    task_out, task_err = task_proc.communicate()
    if isinstance(task_out, bytes):
        task_out = task_out.decode()
    if isinstance(task_err, bytes):
        task_err = task_err.decode()
    task_res = hsp_res.Result(task_proc.returncode, task_out, task_err, task_params)
    if task_res.returncode:
        raise hsp_err.HeasoftpyExecutionError(task_args[0], task_res)
    updated_par_contents = read_par_file(par_path)
    par_dict = dict()
    for parm_key in updated_par_contents:
        par_dict[parm_key] = updated_par_contents[parm_key]['default']
    task_res.params = par_dict
    return task_res
