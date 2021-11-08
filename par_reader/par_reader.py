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
                        if not param[6]:
                            param[6] = ''
                        param_dict = {'type':     param[1], 'mode':     param[2],
                                      'default':  typify(param[3].strip(),param[1]),
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

def typify(value, intype):
    """Take input string value and type string and return correctly typed value.

    Need to handle special types in here, like CALDB.
    Currently returns blank strings when confused."""

    #  Some paths, this has already been done.
    if not isinstance(value,str):  return
    value = value.strip()
    if value.find("'") != -1:
        value = value.replace("'", "")
    if value.find('"') != -1:
        value = value.replace('"', '')
    if value == 'INDEF' and (intype == 'r' or intype == 'i'):
        return None
    if len(value) == 0:
        return ''
    if intype == 'fw':
        return
    try:
        # Note that type_switch(intype) returns a type conversion function
        # (such as int()).
        converter_fn = type_switch(intype.strip())
        return converter_fn(value)
    except:
        print('WARNING:  Could not convert "{0}" to "{1}"'.format(value, intype))
        return value


def type_switch(arg):
    "A switch on the input type string to return the Python type"
    switcher = { 'i': int, 's': str , 'f': str, 'b': bool,
                 'r': float, 'fr':str, 'd': str}
    try:
        return switcher.get(arg)
    except:
        sys.exit("Error!  don't understand the type {arg} in the pfile")

