"""
Python interface for HEAsoft's All-purpose Parameter Environment
"""
import collections
import csv
import sys

def read_par_file(par_path):
    """
    Reads a par file, returning the contents as a dictionary with the parameter
    names as keys.
    """
    par_contents = collections.OrderedDict()
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
