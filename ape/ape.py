import inspect
import re, os, sys, traceback
import collections
import csv
import sys
import heasoftpy.core.errors as hsp_err
import heasoftpy.core.result as hsp_res
import heasoftpy.utils as hsp_utils
#import __main__


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
                                      'default':  hsp_utils.typify(param[3].strip(),param[1]),
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


class params(collections.OrderedDict):
    """ Parameter object for heasoftpy that works like a smart dictionary.
    """
    def __enter__(self,inarg=None):
        """ Called when you enter a with statement """
        return self
        
    def __exit__(self, exc_type, exc_value, tb):
        """ Called when you exit the with statement """
        if exc_type is not None:
            traceback.print_exception(exc_type, exc_value, tb)
            return False
        self._write_par_file()
        return True


    def __init__(self,inarg=None,name=None,**kwargs):
        """Here there be brains to figure out what was given and what to do with it

        Note that if you call only params(arg), then arg should be a dictionary or 
        params object. If you need to specify the name, always use name="myname".  
        """

        #  First figure out the context. It would be good to get something here
        #  that works generally rather than have to be given the name.     
        if name is None:
            curframe = inspect.currentframe()
            calframe = inspect.getouterframes(curframe, 2)
            self.exename=calframe[1][3]
            print(f"WARNING:  no name given, and inspect thinks I'm {self.exename}.")
        else:
            self.exename = name

        #  Get whatever was passed in
        self.kwargs=kwargs
        #  Get what's in the user or system pfile
        self.parfile_dict = self._read_par_file()

        #  If you give no arguments, use pfile dictionary
        if inarg is None and len(kwargs) == 0:
            collections.OrderedDict.__init__(self,self.parfile_dict)
        #  If you give a dictionary, init the params() object from it
        #  If you give it another params object, init off of it
        elif type(inarg) is dict or type(inarg) is params:
            collections.OrderedDict.__init__(self,inarg)
        #  If you specify as keyword arguments:
        elif len(kwargs) > 0:
            if not self._process_kwargs():
                print("ERROR:  cannot initialize params object from kwargs")
                raise ValueError
        else:
           print("ERROR:  cannot initialize params object from {inarg}")
           raise ValueError

        #  Now query for anything else (and converts values from dict to value type).  
        self._query_args()


    def _read_par_file(self):
        "Read in the pfile to a dictionary"
        par_path=hsp_utils.get_pfile(self.exename)
        return read_par_file(par_path)        


    def _write_par_file(self):
        """This will write the current params contents to its pfile, used in the exit.

        But the current object may not have the full pfile info, may just be simple 
        key=value pairs.  So have to get that back, update the values, and then write 
        the fulld dictionary.
        """
        print("TO DO:  write current to pfile")
        """par_path=hsp_utils.get_pfile(self.exename,user=True)
        while open(par_path,'w') as pfile:
            writer=csv.writer(pfile,delimiter=',', quotechar='"')
            writer.writerow(
        """

    def _process_kwargs(self):
        args_ok = True
        for kwa in self.kwargs:
            if not kwa == 'stderr':
                if hsp_utils.is_param_ok((kwa, self.kwargs[kwa]), self.parfile_dict):
                    #self.task_args.append('{0}={1}'.format(kwa, self.kwargs[kwa]))
                    #self.task_params[kwa] = self.kwargs[kwa]
                    self[kwa] = self.kwargs[kwa]
                else:
                    args_ok = False
                    print( 'Error! The {} parameter was not specified correctly. ' \
                    'Please correct and try again.'.format(kwa))
        if 'stderr' in self.kwargs:
            if self.kwargs['stderr']:
                self.stderr_dest = subprocess.PIPE
        return args_ok


    def _query_args(self):
        """Queries user for parameters depending on settings.

        Note that the value of each key may be a dictionary going into this
        and is a simple value coming out.
        """
        params_not_specified = []
        for entry in self.parfile_dict:
            if not entry in self.kwargs:
                if hsp_utils.check_query_param(entry, self.parfile_dict):
                    params_not_specified.append(entry)
                else:
                    self[entry]=self.parfile_dict[entry]['default']
        for missing_param in params_not_specified:
            param_val = hsp_utils.ask_for_param(missing_param, self.parfile_dict)
            self[missing_param] = param_val
