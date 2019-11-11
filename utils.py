"""
Utilities for the heasoftpy module, generally intended for use by the module,
not called by users.
"""

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
        return not (self.__eq__(other))

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
