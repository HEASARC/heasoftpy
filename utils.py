"""
Utilities for the heasoftpy module, intended for use by the module, not called
by users.
"""

import sys

def _ask_for_param(p_name, p_dict):

    if 'prompt' in p_dict[p_name]:
        query_msg = 'No value found for {0}.\n{1}'.format(p_name, p_dict[p_name]['prompt'])
    else:
        query_msg = 'No value found for {0}.\nPlease enter: '.format(p_name)
    usr_inp = ''
    while not usr_inp:
        try:
            usr_inp = input(query_msg)
        except EOFError:
            sys.exit('\nKeyboard interrupt received, program stopping.')
    return usr_inp
