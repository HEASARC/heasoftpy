"""
Python interface to the HEASoft APE library (which was made to replace/be compatible with
the PIL (Parameter Interface Library).
"""

import collections
#import csv
#import inspect     # May need to add this back in later
#import os
#import re
import subprocess
#import sys
import traceback

#import heasoftpy.core.errors as hsp_err
#import heasoftpy.core.result as hsp_res
import heasoftpy.utils as hsp_utils
from  ..par_reader import read_par_file

#import __main__

class ApeParamsException(Exception):
    """ A simple custom class for exceptions from the Params class """
    def __init__(self, msg=None):
        super().__init__(msg)
        if msg:
            if msg.upper().find('ERROR') == -1:
                self.message = ' '.join(['ERROR: ', msg])
            else:
                self.message = msg
        else:
            self.message = 'ERROR: Encountered a Params error.'

class Params(collections.OrderedDict):
    """
    Parameter object for heasoftpy that works like a smart dictionary.
    """
    def __enter__(self,inarg=None):
        """ Called when you enter a with statement """
        return self

    def __exit__(self, exc_type, exc_value, tr_bk):
        """ Called when you exit the with statement """
        if exc_type is not None:
            traceback.print_exception(exc_type, exc_value, tr_bk)
            return False
        self._write_par_file()
        return True


    def __init__(self,inarg=None,name=None,**kwargs):
        """
        Here there be brains to figure out what was given and what to do with it

        Note that if you call only params(arg), then arg should be a dictionary or
        params object. If you need to specify the name, always use name="myname".
        """

        # TO DO: Figure out how to make this part work ... if it can be done
        #  First figure out the context. It would be good to get something here
        #  that works generally rather than have to be given the name.
        # if name is None:
        #     curframe = inspect.currentframe()
        #     calframe = inspect.getouterframes(curframe, 2)
        #     self.exename=calframe[1][3]
        #     print("WARNING:  no name given, and inspect thinks I'm {}.".format(self.exename))
        # else:
        #     self.exename = name

        if name:
            self.exename = name
        else:
            raise ApeParamsException('No name specified in Params instantiation.')

        #  Get whatever was passed in
        self.kwargs = kwargs
        #  Get what's in the user or system pfile
        self.parfile_dict = self._read_par_file()

        ### TESTING CODE ###
#        print('After _read_par_file, self.parfile_dict:', self.parfile_dict)

        #  If you give no arguments, use pfile dictionary
        if inarg is None and len(kwargs) == 0:
            collections.OrderedDict.__init__(self,self.parfile_dict)
        # If another Params object or a dictionary is passed in, init
        # the (new) Params object from it.
        elif isinstance(inarg, (dict, Params)):
            collections.OrderedDict.__init__(self,inarg)
        #  If keyword arguments are passed in:
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
        """ Read in the pfile to a dictionary """
        par_path = hsp_utils.get_pfile(self.exename)
        return read_par_file(par_path)


    def _write_par_file(self):
        """This will write the current params contents to its pfile, used in the exit.

        But the current object may not have the full pfile info, may just be simple
        key=value pairs.  So have to get that back, update the values, and then write
        the fulld dictionary.
        """
        # TO DO:  write current to pfile
        print("TO DO:  write current to pfile")
        # par_path=hsp_utils.get_pfile(self.exename,user=True)
        # while open(par_path,'w') as pfile:
        #     writer=csv.writer(pfile,delimiter=',', quotechar='"')
        #     writer.writerow(

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
