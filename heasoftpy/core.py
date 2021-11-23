
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
        
        # to handle "_" and "-" in names, we also create pyname
        self.name   = name
        self.pyname = name.replace('-', '_')
            
        
        # first read the par file as a starter
        pfile  = HSPTask.find_pfile(name)
        params = HSPTask.read_pfile(pfile)
     
        # add extra useful keys
        default_mode = params['mode']['default'] if 'mode' in params.keys() else 'h'
        for pname, pdesc in params.items():
            isReq = 'q' in pdesc['mode'] or ('a' in pdesc['mode'] and 'q' in default_mode)
            pdesc['required'] = isReq
        
        self.all_params = params
        self.params = None
        self.pfile = pfile
        self.__doc__ = self._generate_fcn_docs()

    
    def __call__(self, args=None, **kwargs):
        """Call the task.
        
        There are several ways to call HSPTask:
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
        
        # create a dict for all model parameters
        usr_params = {p:pdesc['default'] for p,pdesc in self.all_params.items()}
        usr_params.update(params)
        self.params = usr_params
        
        
        # do_exec is a hidden parameter used for debugging and testing
        # Set to True, unless we are testing and debugging.
        do_exec = kwargs.get('do_exec', True)
        if do_exec:
            # disable prompt: https://heasarc.gsfc.nasa.gov/lheasoft/scripting.html
            os.environ['HEADASNOQUERY'] = ''
            os.environ['HEADASPROMPT'] = '/dev/null'
            
            result = self.exec_task()
            
            # write new params to the user .par file
            usr_pfile = HSPTask.find_pfile(self.name, return_user=True)
            HSPTask.write_pfile(usr_pfile, self.params, self.all_params)
            
            # now we are ready to call the task
            return result
    
    
    def exec_task(self):
        """Run the Heasoft task
        
        This method can be overriden by python-only tasks that subclass HSPTask
        The task parameters are available in:
            self.params: a dict of {par:value} parameters provided by the user
                
        Here, we just call the heasoft task as a subprocess
                
        Returns:
            This method should return HSPResult object.
            e.g. HSPResult(ret_code, std_out, std_err, params)
        
        """
        
        # put the parameters in to a list of par=value
        usr_params = self.params
        
        cmd_params = [f'{par}={val}' for par,val in usr_params.items()]
        
        # the task executable
        exec_cmd = os.path.join(os.environ['HEADAS'], f'bin/{self.name}')
        cmd_list = [exec_cmd] + cmd_params
        proc = subprocess.Popen(cmd_list, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        proc_out, proc_err = proc.communicate()
        
        if isinstance(proc_out, bytes): 
            proc_out = proc_out.decode()
        if isinstance(proc_err, bytes): 
            proc_err = proc_err.decode()
        
        return HSPResult(proc.returncode, proc_out, proc_err, usr_params)
    
    
    def task_docs(self):
        """Print docstring help specific to this task
        
        For standard tasks, this uses fhelp to get the docs,
        for python-only tasks, classes subclassing HSPTask can
        provide a task_docs method that return a string with the
        docs.
        
        
        Return:
            str of documentation
        
        """
        name = self.name
        
        # call fhelp; assume HEADAS is defined #
        cmd  = os.path.join(os.environ['HEADAS'], 'bin/fhelp')
        try:
            proc = subprocess.Popen([cmd, f'task={name}'], stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            proc_out, proc_err = proc.communicate()
        except:
            print(f'Failed in running fhelp to obtain docs for {name}')
        # ---------- #

        # convert fhelp output from byte to str #
        try:
            if proc_err is None or len(proc_err) != 0:
                raise RuntimeError
            else:
                fhelp = proc_out.decode()
                fhelp = f"{'-'*50}\n   The following has been generated from fhelp\n{'-'*50}\n{fhelp}"
        except:
            # we can be more specific in trapping
            fhelp = f'No fhelp text was generated for {name}'
        fhelp.replace('"""', '')
        # ------------------------------------- #
        
        return fhelp
    
    
    def build_params(self, user_pars):
        """Check the user given parameters agains the expectation from the .par file.

        - Loop through the expected task parameters (self.all_params).
        - Update their value if any of them is given by the user (in user_pars)
        - if a parameter is required by the task and not given, query the user
        The final updated list of parameters is returned
        
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
                params[pname] = HSPTask.param_type(user_pars[pname], pdesc['type'])
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
    def write_pfile(pfile, usr_params, all_params):
        """Write .par file of some task, typically after executing
        
        Args:
            pfile: path and name of the .par file. If it doesn't exist, create it
            usr_params: dict of par:value supplied by user to be updated
            all_params: OrderedDict of par:desc containing all parameters of the task
            
        Return:
            None
        
        """
        
        # check the file exists or create one #
        if not os.path.exists(pfile):
            try:
                open(pfile, 'w').write('')
            except:
                raise IOError(f'Cannot write to {pfile}. Check folder and permission')
            old_params = all_params
        else:
            old_params = HSPTask.read_pfile(pfile)
        
        # check that all_params and params in existing .par are consistent
        if len(old_params) != len(all_params):
            raise HSPTaksExecption(f'Number of parameters in all_params '
                                   f'({len(all_params)}) differ from those '
                                   'in existing {pfile} ({len(old_params)})')
        # ----------------------------------- #
        
        # update previous pars with those given by user #
        for pname,pval in usr_params.items():
            if pname in all_params:
                all_params[pname]['default'] = pval
            else:
                print(f'parameter {pname} does not exist in task parameter list. Skipping')
        # --------------------------------------------- #
        
        
        # make any style changes to the values to be printed #
        for pname, pdesc in all_params.items():
            if pdesc['type'] == 's':
                pdesc['default'] = f'\"{pdesc["default"]}\"'
        # -------------------------------------------------- #
        
        
        # now write the updated parameter list #
        ptxt = '\n'.join([f'{pname},{pdesc["type"]},{pdesc["mode"]},'
                          f'{pdesc["default"]},{pdesc["min"]},{pdesc["max"]},'
                          f'\"{pdesc["prompt"]}\"'
                          
                          for pname,pdesc in all_params.items()])
        with open(pfile, 'w') as pf:
            pf.write(ptxt)
        # ------------------------------------ #
        
        
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
            par   = {key: info[ikey+1].strip().strip('"') for ikey,key in enumerate(pkeys)}
            
            for k in ['default']:
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
        
        if inType in ['r', 'i']:
            value = str(value).replace("'", "").replace('"', '')
        
        
        # now proceed with the conversion
        switcher = { 'i': int, 's': str , 'f': str, 'b': bool,
                     'r': float, 'fr':str, 'd': str, 'g': str, 'fw': str}
        
        if not inType in switcher.keys():
            raise ValueError(f'parameter type {inType} is not recognized.')
        
        # TODO: more error trapping here
        result = switcher[inType](value)
        
        # keep boolean as yes/no not True/False
        if inType == 'b':
            result = 'yes' if result else 'no'
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
        
        
    def _generate_fcn_docs(self):
        """Generation standard function docstring from .par file

        Additional help is generated by task_docs, which, in the case of heasoft
        tools, is generated with fhelp

        """


        name = self.name
        params = self.all_params

        # parameter description #
        parsDesc = '\n'.join([
                        f'     {par:12} {"(Req)" if desc["required"] else "":6}: '
                        f'{desc["prompt"]} (default: {desc["default"]})'
            for par,desc in params.items()])
        # --------------------- #

        # get extra docs from the task #
        task_docs = self.task_docs()

        # put it all together #
        docs = f"""
    Automatically generated function for Heasoft task {name}.
    Additional help may be provided below.

    Args:
{parsDesc}
\n\n
{task_docs}
        """
        return docs

    def generate_fcn_code(self):
        """Create python function for task_name

        """
        task_name   = self.name
        task_pyname = self.pyname

        # generate docstring
        docs = self._generate_fcn_docs()

        # generate function text
        fcn = f"""

import sys
import os
import subprocess

if __name__ == '__main__':
    # this will be updated depending on where we want this installed
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
    from heasoftpy.core import HSPTask, HSPTaskException
    from heasoftpy.utils import process_cmdLine
else:    
    from ..core import HSPTask, HSPTaskException



def {task_pyname}(args=None, **kwargs):
    r\"""
{docs}
    \"""

    {task_pyname}_task = HSPTask(name="{task_name}")
    return {task_pyname}_task(args, **kwargs)


if __name__ == '__main__':
    {task_pyname}_task = HSPTask(name="{task_name}")
    cmd_args = process_cmdLine({task_pyname}_task)
    {task_pyname}_task(**cmd_args)

        """

        return fcn
    
    

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
        
        txt  = ('-'*21) + '\n:: Execution Result ::\n' + ('-'*21)
        txt += f'\n> Return Code: {self.ret_code}'
        txt += f'\n> Output:\n{self.std_out}'
        txt += f'\n> Errors: {(self.std_err if self.std_err else "None")}'
        ptxt = '\n\t'.join([f'{par:10}: {val}' for par,val in self.params.items()])
        txt += f'\n> Parameters:\n\t{ptxt}'
        return txt
    
    def __repr__(self):
        return self.__str__()