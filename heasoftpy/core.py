
from collections import OrderedDict
import subprocess
import os
import re

from . import utils 


class HSPTaskException(Exception):
    """A simple exception class"""
    
    def __init__(self, errMsg=None):
        super(HSPTaskException, self).__init__(errMsg)


class HSPTask:
    """A class for handling a Heasoftpy (HSP) task"""

    def __init__(self, name=None):
        """Initialize an HSPTask with a given name.
        
        Args:
            name (str): The name of the task to be called. Required
                
        """
        
        # task name is required #
        if name is None:
            raise HSPTaskException('Task name is required')
        else:
            self.name = name
            
        
        # first read the par file as a starter
        pfile  = HSPTask.find_pfile(name)
        params = HSPTask.read_pfile(pfile)
        self.all_params = params
        
    
    def __call__(self, args=None, **kwargs):
        """Call the task.
        
        There are several ways to call HSPTaks:
        1: HSPTask(): query parameters as usually done with heasoft tasks
        2: HSPTask(previousHSPTask): initialize from a previously defined HSPTask
        3: HSPTask(argsDict): args is a dict or OrderedDict of input parameters
        4: HSPTask(foo=bar, x=0): parameters are passed in the kwargs dict.
        
        
        Args:
            args (HSPTask, dict, OrderedDict): task parameters as another HSPTask,
                dict or OrderedDict
            **kwargs: individual task parameters given as: paramter=value.
            
        Returns:
            
        """
        
        # assemble the user input, if any, into a dict
        if args is None:
            user_pars = {}
        elif isinstance(args, (dict, OrderedDict)):
            user_pars = dict(args)
        elif isinstance(args, HSPTask):
            user_pars = dict(args.params)
        else:
            raise HSPTaskException('Unrecognized input in initializing HSPTask')
        
        # add all keywords if present
        # any commandLine arguments in sys.argv should be passed in kwargs
        user_pars.update(kwargs)
        
        # now check the user input against expectations, and query if incomplete
        params = self.build_params(user_pars)
        self.params = params
        
        # now we are ready to call the task 
    
    
    def build_params(self, user_pars):
        """Check the user given parameters agains the expectation from the .par file.

        - Loop through the expected task parameters (self.params).
        - Update their value if any of them is given by the user (in user_pars)
        - if a parameter is required by the task and not given, query the user
        The final updated list of parameters is in self.params
        
        Args:
            user_pars: a dict containing the par_name:value given by the user
            
        Returns:
            dict of {pname:pvalue} for the values either passed by user or queried if required
        """
        
        # loop through task parameters and either:
        params = {}
        default_mode = params['mode']['default'] if 'mode' in params.keys() else 'h'
        for pname, pdesc in self.all_params.items():
            
            isReq = 'q' in pdesc['mode'] or ('a' in pdesc['mode'] and 'q' in default_mode)
            
            if pname in user_pars:
                params[pname] = user_pars[pname]
            elif isReq:
                # query parameter
                params[pname] = HSPTask.query_param(self.name, pname, pdesc)
            else:
                # parameter not needed and not given
                pass
        return params
    
    
    @staticmethod
    def query_param(taskname, pname, pdesc):
        """Query the user for parameter pname in task taskname
        
        Args:
            taksname: name of the task
            pname: name of the parameter
            pdesc: a dict containing the description of the paramter
        
        Return:
            The queried parameter value
            
        TODO: handle nan, None, INDEF etc
            
        """
        querymsg = f':: {taskname}:{pname} ::\n{pdesc["prompt"]} ({pdesc["default"]}) > '
        done = False
        while not done:
            
            user_inp = input(querymsg)
            
            # special cases
            if user_inp == '':
                user_inp = pdesc['default']
            if pdesc['type'] == 'b':
                user_inp = 'no' if user_inp.lower() in ['n', 'no', 'false'] else 'yes'
            
            try:
                user_inp = HSPTask.param_type(user_inp, pdesc['type'])
                done = True
            except ValueError:
                print(f'value {user_inp} cannot be processed. Try again!')
        return user_inp
    
        
    @staticmethod
    def read_pfile(pfile):
        """Read a par file for some task
        
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
        """Find the correct type from pfiles
        
        Args:
            value: The value to be converted; typically a str
            inType: a str representing the type in the .par files.
                One of: {i, s, f, b, r, fr, b}
        
        Returns:
            the value in the correct type
        
        """
        
        # handle special cases first
        if not isinstance(value, str):
            # already done
            return value
        
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
    
    
    @staticmethod
    def find_pfile(name, return_user=False):
        """search for an return the .par file for the task
        
        Args:
            name: Name of the task, so the pfile is {name}.par
            return_user: return the user pfile, even if it doesn't exist
                User pfile is the taken from the first entry to PFILES
        
        Returns:
            the path to the {name}.par pfile
        
        """
        
        if 'HEADAS' in os.environ:
            sys_pfile = os.path.join(os.environ['HEADAS'], 'syspfiles', f'{name}.par')
        else:
            raise HSPTaskException('HEADAS not defined. Please initialize Heasoft!')
            
        # split on both (:,;)
        pfiles = re.split(';|:', os.environ['PFILES'])
        
        # check a .par file exists anywhere
        found = False
        for pf in pfiles:
            if os.path.exists(os.path.join(pf, f'{name}.par')):
                found = True
                break
        if not found:
            raise HSPTaskException(f'No .par file found for task {name}')
        
        # user pfile; assumed to be the first one in pfiles
        loc_pfile = os.path.join(pfiles[0], f'{name}.par')
    
        # not strictly accurate, but use it for now
        pfile = loc_pfile if (os.path.exists(loc_pfile) or return_user) else sys_pfile
        return pfile
            