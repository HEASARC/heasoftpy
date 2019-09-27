"""
Utilities for the heasoftpy module, intended for use by the module, not called
by users.
"""

import sys

def _ask_for_param(p_name, p_dict):

    if 'prompt' in p_dict[p_name]:
        query_msg = '{1}'.format(p_name, p_dict[p_name]['prompt']+'> ')
    else:
        query_msg = 'No value found for {0}.\nPlease enter: '.format(p_name+' > ')
    usr_inp = ''
    while not usr_inp:
        try:
            usr_inp = input(query_msg)
        except EOFError:
            sys.exit('\nKeyboard interrupt received, program stopping.')
    return usr_inp

def _check_query_param(p_name, p_dict):
    """
    checks whether a user should be queried for a parameter value if parameter not specified
    see https://heasarc.gsfc.nasa.gov/docs/software/lheasoft/headas/pil/node12.html
    :param p_name: parameter name
    :param p_dict: parameter dictionary for function
    :return: True if user needs to be queried for parameter value, False if not
    """
    ans= False
    if 'a' in p_dict[p_name]['mode']:
        if 'q' in p_dict['mode']['default']:
            ans = True
    if 'q' in p_dict[p_name]['mode']:
        ans = True
    return ans

