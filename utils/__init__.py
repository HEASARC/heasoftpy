"""
Utilities for the heasoftpy module, generally intended for use by the module,
not called by users.
"""

import csv
import os
import sys

class ProgramVersion():
    """
    Methods for comparing version numbers, which allow use of the symbols less
    than (<), greater than (>), equals (=) and not equals (!=). The versions
    must be made up of only numeric digits and dots (periods), e.g. "6.9.42".
    Other characters will fail upon instantiation.
    """
    def __init__(self, ver):
        self.version = ver
        parts = self.version.split('.')
        self.ver_parts = list()
        for part in parts:
            try:
                self.ver_parts.append(int(part))
            except ValueError:
                err_msg = 'Error! Could not parse {0} (could not convert {1} to integer).'.\
                          format(self.version, part)
                sys.exit(err_msg)

    def __eq__(self, other):
        if len(self.ver_parts) == len(other.ver_parts):
            for ndx in range(len(self.ver_parts)):
                if self.ver_parts[ndx] != other.ver_parts[ndx]:
                    return False
        else:
            return False
        return True

    def __gt__(self, other):
        max_parts = max(len(self.ver_parts), len(other.ver_parts))
        for ndx in range(max_parts):
            if ndx < len(self.ver_parts):
                self_part = self.ver_parts[ndx]
            else:
                self_part = 0
            if ndx < len(other.ver_parts):
                other_part = int(other.ver_parts[ndx])
            else:
                other_part = 0
            if self_part > other_part:
                return True
        return False

    def __lt__(self, other):
        max_parts = max(len(self.ver_parts), len(other.ver_parts))
        for ndx in range(max_parts):
            if ndx < len(self.ver_parts):
                self_part = self.ver_parts[ndx]
            else:
                self_part = 0
            if ndx < len(other.ver_parts):
                other_part = int(other.ver_parts[ndx])
            else:
                other_part = 0
            if self_part < other_part:
                return True
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

def ask_for_param(p_name, p_dict):
    """
    Asks user for parameter named in p_name.

    :param p_name: parameter name
    :param p_dict: parameter dictionary for function
    :return: The user input
    """
    if 'prompt' in p_dict[p_name]:
        query_msg = '{0}'.format(p_dict[p_name]['prompt']+'> ')
    else:
        query_msg = 'No value found for {0}.\nPlease enter: '.format(p_name+' > ')
    usr_inp = ''
    while not usr_inp:
        try:
            usr_inp = input(query_msg)
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
#    print('checking {}'.format(param[0]))
    if param[0] in par_dict:
#        print('Maybe')
#        print(par_dict[param[0]])
        param_type = par_dict[param[0]]['type']
        if param_type == 's':
            # Is the following redundant? Everything will be a string when it "arrives"  ...
#            print('Testing for string')
            if isinstance(param[1], str):
#                print('{} is a string'.format(param[1]))
                param_ok = True
        elif param_type == 'i':
#            print('Testing {} as int.'.format(param[1]))
            try:
                _ = int(param[1])
                param_ok = True
#                print('{} is an int'.format(param[1]))
            except ValueError:
                #pass
                print('ValueError encountered converting "{}" to int'.format(param[1]))
        elif param_type == 'b':
            if isinstance(param[1], str):
                param_lower = param[1].lower()
                if param_lower in ['y', 'yes', 'n', 'no']:
                    param_ok = True
#            print('Testing for boolean')
            # To do: Figure what what is acceptable here. They seem to want "y", "n", "t", "f",
            # "1", "0", etc. to be acceptable ...
        elif param_type == 'r':
#            print('Testing for real')
            try:
                _ = float(param[1])
                param_ok = True
#                print('{} is an float'.format(param[1]))
            except ValueError:
                #pass
                print('ValueError encountered converting "{}" to float'.format(param[1]))
        elif param_type.find('f') != -1:
#            print('Testing for filename')
            ### For now, checking for str. To do: find out what needs to be do for a "file type"
            if isinstance(param[1], str):
#                print('{} is a string'.format(param[1]))
                param_ok = True
    else:
        print('Error! Invalid parameter type {}'.format(param[0]))
    return param_ok

def read_version(module_dir):
    """
    Returns a string containing the version, as read from the version file.
    """
    full_module_dir = os.path.abspath(module_dir)
    ver_str = None
    ver_path = os.path.join(full_module_dir, 'version')
    if os.path.exists(ver_path):
        with open(ver_path, 'rt') as ver_file:
            try:
                ver_str = str(ver_file.read())
            except:
                err_msg = 'Error! Could not read file "version" in the {} directory.'.format(full_module_dir)
                sys.exit(err_msg)
    else:
        err_msg = 'Error! Could not locate file "version" in the {} directory.'.format(full_module_dir)
        sys.exit(err_msg)
    return ver_str
