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
import sys
import traceback

#import heasoftpy.core.errors as hsp_err
#import heasoftpy.core.result as hsp_res
import heasoftpy.utils as hsp_utils
from  ..par_reader import read_par_file, type_switch, typify

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
    Parameter object for heasoftpy, an OrderedDict with extra functions.
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


    def __init__(self,inarg=None,name=None,init_mode=None,**kwargs):
        """
        Here there be brains to figure out what was given and what to do with it.

        A module will be called as 

            def mymodule(inpars=None,**kwargs):
                if inpars and type(inpars) is Params:
                    pars = Params(inpars,name="mymodule")
                else:
                    pars = Params(**kwargs,name="mymodule")

        The executable for mymodule will have a main function that is basically:  

            with Params(name="tjtest1") as pars:  
                try:
                    result=tjtest1(pars)


        Case 1:  Params(previousParams)  a complete Params object or OrderedDict
        Case 2:  Params({"foo":"bar","x":0})  i.e., a simple dictionary
        Case 3:  Params(foo='bar',x=0)  i.e., passed in through kwargs
        Case 4:  nothing given on init but on command-line in argv
        Case 5:  nothing give on init or command-line;  query as usual

        Possible mixes:  Cases 2, 3, and 5 can give a partial list of parameters.  
        The parameter file will be read to fill in the others, querying the user 
        if appropriate.

        (Do we need 2 and 3?  kwargs is both.)  
        """

        if name:
            self.exename = name
        else:
            raise ApeParamsException('No name specified in Params instantiation.')

        if type(inarg) is Params or type(inarg) is collections.OrderedDict:
            # Case 1:  Do nothing but init the current dictionary from it
            collections.OrderedDict.__init__(self,inarg)
        elif type(inarg) is dict:
            # Case 2:  read in pfile into self, replace with input dictionary
            #  values, then query for any remaining
            collections.OrderedDict.__init__(self,self._read_par_file())
            for k,v in inarg.items():  self[k]['default']=v
            self._query_args(inarg) 
        elif len(kwargs) > 0:
            # Case 3:  read in pfile into self, then replace any specified 
            #   with kwargs, then query for any remaining.  
            collections.OrderedDict.__init__(self,self._read_par_file())
            self._process_inputs(kwargs)
            self._query_args(kwargs) 
        elif len(sys.argv) > 1:
            # Case 4:  read in pfile into self, then replace with argv,
            #  then query for any remaining.  
            collections.OrderedDict.__init__(self,self._read_par_file())
            inargs=self._get_command_line_args()
            self._query_args(inargs) 
        elif len(sys.argv) == 1 and not kwargs and not inarg:
            # Case 5:  read in pfile into Params and query as appropriate
            collections.OrderedDict.__init__(self,self._read_par_file())
            if init_mode is not 'h':
                self._query_args()             
        else:  
            # confused
            raise ApeParamsException(
                f"""Confused by inputs:\n  inarg={inarg},\n  
                kwargs={kwargs},\n  sys.argv={sys.argv}."""
            )

        self._fix_types()
        return

    def _fix_types(self):
        "Depending on the path above, these have already been typified"
        for param in self:
            if isinstance(self[param]['default'],str):
                thistype = self[param]['type']
                thisval = self[param]['default'] 
                self[param]['default'] = typify(thisval,thistype)               


    def _read_par_file(self):
        """ Read in the full pfile to an Ordered Dict like in Params """
        par_path = hsp_utils.get_pfile(self.exename)
        return read_par_file(par_path)


    def _write_par_file(self):
        """This will write the current params contents to its pfile, used in the exit.

        But the current object may not have the full pfile info, may just be simple
        key=value pairs.  So have to get that back, update the values, and then write
        the fulld dictionary.
        """
        # TO DO:  write current to pfile
        print("TO DO:  write current Params to pfile")
        # par_path=hsp_utils.get_pfile(self.exename,user=True)
        # while open(par_path,'w') as pfile:
        #     writer=csv.writer(pfile,delimiter=',', quotechar='"')
        #     writer.writerow(

    def _process_inputs(self, indict):
        """Looks at inputs and resets self  as needed"""
        for param in indict.keys():
            if not param == 'stderr':
                if hsp_utils.is_param_ok((param, indict[param]), self):
                    self[param]['default'] = indict[param]
                else:
                    ApeParamsException(f"Error! The {param} parameter was not specified correctly.")
        if 'stderr' in indict:
            if indict['stderr']:
                self.stderr_dest = subprocess.PIPE


    def _query_args(self, indict=None):
        """Queries user for parameters depending on settings.  

        Used by init when kwargs or argv become the indict.  When called,
        self should already be an OrderedDict filled with the parameter file.  
        """
        if not indict:  indict={}
        for param in self:
            if not param in indict and hsp_utils.check_query_param(param, self):
                param_val = hsp_utils.ask_for_param(param, self)
                self[param]['default'] = param_val


    def _get_command_line_args(self):
        """ Looks at argv for key=vale pairs to read, resets self as necessary"""
        import sys
        indict={}
        if len(sys.argv) == 0:
            return
        else:
            for a in sys.argv[1:]:
                x=a.split('=')
                indict[x[0]]=x[1]
        self._process_inputs(indict)
        return indict


    def to_simple_dict(self):
        out={}
        for param in self.keys():
            out[param]=self[param]['default']
        return out

    def update(self, outpars):
        for param in outpars:
            self[param]['default']=outpars[param]
