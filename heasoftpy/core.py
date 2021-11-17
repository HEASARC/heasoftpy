
from collections import OrderedDict
import subprocess
import os

from . import utils 


class HSPTaskException(Exception):
    """A simple exception class"""
    
    def __init__(self, errMsg=None):
        super(HSPTaskException, self).__init__(errMsg)


class HSPTask:
    """A class for handling a Heasoftpy (HSP) task"""

    def __init__(self, name=None, args=None, **kawrgs):
        """Create an HSPTask with a given name.
        
        There are several ways to initialize HSPTaks:
        1: HSPTask(name): query parameters as usually done with heasoft tasks
        2: HSPTask(name, previousHSPTask): initialize from a previously defined HSPTask
        3: HSPTask(name, argsDict): args is a dict or OrderedDict of input parameters
        4: HSPTask(name, foo=bar, x=0): parameters are passed in the kwargs dict.
        
        
        Args:
            name (str): The name of the task to be called. Required
            args (HSPTask, dict, OrderedDict): task parameters as another HSPTask,
                dict or OrderedDict
            **kwargs: individual task parameters given as: paramter=value.
            
        Returns:
            
            
        Examples:
            TODO.
            
        """
        
        # task name is required #
        if name is None:
            raise HSPTaskException('Task name is required')
        else:
            self.name = name
        
        
    @staticmethod
    def read_pfile(pfile):
        """Read a par file from some task
        
        Can be called without initializing HSPTask by doing: HSPTask.read_pfile(...)
        
        Args:
            pfile: full path to .par file
            
        Returns:
            OrderedDict
        
        """
        
        if not os.path.exists(pfile):
            raise IOError(f'parameter file {pfile} not found')
        
        params = OrderedDict()
        for line in open(pfile, 'r'):
            
            # make sure we have a line with information
            info = line.strip().split(',')
            if line.startswith('#') or len(info) < 6:
                continue
            
            # extract information about the parameter
            pname = info[0]
            pkeys = ['type', 'mode', 'default', 'min', 'max', 'prompt']
            par   = {key: info[ikey+1].strip('"').strip() for ikey,key in enumerate(pkeys)}
            
            for k in ['default', 'min', 'max']:
                par[k] = HSPTask.param_type(par[k], par['type'])
            
            params[pname] = par
        return params
    
    
    @staticmethod
    def param_type(value, inType):
        """Find the correct type from pfiles"""
        
        # handle special cases first
        if value == 'INDEF' and inType in ['r', 'i']:
            return None
        
        if value == '' and inType in ['r', 'i']:
            value = 0
            
        if inType == 'b':
            value = 1 if value.lower() in ['yes', 'true'] else 0
        
        
        # now proceed with the conversion
        switcher = { 'i': int, 's': str , 'f': str, 'b': bool,
                     'r': float, 'fr':str, 'd': str}
        
        if not inType in switcher.keys():
            raise ValueError(f'arameter type {inType} is not recognized')
        
        # TODO: more error trapping here
        result = switcher[inType](value)
        return result
        