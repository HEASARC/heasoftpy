
from collections import OrderedDict
import subprocess
import os
import re


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
     
        # add extra useful keys
        default_mode = params['mode']['default'] if 'mode' in params.keys() else 'h'
        for pname, pdesc in params.items():
            isReq = 'q' in pdesc['mode'] or ('a' in pdesc['mode'] and 'q' in default_mode)
            pdesc['required'] = isReq
        
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
        # do_exec is a hidden parameter used for debugging and testing
        # it should be set to False when calling for testing and debuggin
        do_exec = kwargs.get('do_exec', True)
        if do_exec:
            result = self.exec_task()
            print(result)
    
    
    def exec_task(self):
        """Run the Heasoft task"""
        
        # put the parameters in to a list of par=value
        all_params = self.all_params
        usr_params = self.params
        
        cmd_params = [f'{par}={val}' for par,val in usr_params.items()]
        
        # the task executable
        exec_cmd = os.path.join(os.environ['HEADAS'], f'bin/{self.name}')
        cmd_list = [exec_cmd] + cmd_params
        print(cmd_params)
        proc = subprocess.Popen(cmd_list, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        proc_out, proc_err = proc.communicate()
        
        if isinstance(proc_out, bytes): 
            proc_out = proc_out.decode()
        if isinstance(proc_err, bytes): 
            proc_err = proc_err.decode()
        
        return HSPResult(proc.returncode, proc_out, proc_err, usr_params)
    
    
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
        aParams = self.all_params
        params  = {}
        for pname, pdesc in self.all_params.items():
            
            isReq = pdesc['required']
            
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
        

class HSPResult:
    """Container for the result of a task execution"""
    
    def __init__(self, ret_code, std_out, std_err=None, params=None):
        """Create a result object to summarize the return of a task
        
        
        Args:
            ret_code: return code from running the task
            std_out: The returned string in standard output
            std_err: The returnd standard error, or None
            params: a dict and OrderedDict containing the task parameters
        
        """
        
        self.ret_code = ret_code
        self.std_out  = std_out
        self.std_err  = std_err
        self.params   = params
        
    def __str__(self):
        """Print the result object in a clean way"""
        
        txt  = ('-'*21) + '\n:: Excution Result ::\n' + ('-'*21)
        txt += f'\n> Return Code: {self.ret_code}'
        txt += f'\n> Output:\n{self.std_out}'
        txt += f'\n> Errors: {(self.std_err if self.std_err else "None")}'
        ptxt = '\n\t'.join([f'{par:10}: {val}' for par,val in self.params.items()])
        txt += f'\n> Parameters:\n\t{ptxt}'
        return txt