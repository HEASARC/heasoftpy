# Copyright 2024, University of Maryland, All Rights Reserved

import subprocess
import os
import re
import sys
import io
import selectors
import logging


if '__INSTALLING_HSP' not in os.environ:
    from astropy.utils.exceptions import AstropyDeprecationWarning

    class HSPDeprecationWarning(AstropyDeprecationWarning):
        """heasoftpy Deprecation warning"""


class HSPTaskException(Exception):
    """heasoftpy exception class"""


class HSPTask:
    """A class for handling a Heasoftpy (HSP) task"""

    def __init__(self, name=None):
        """Initialize an HSPTask with a given name.

        Parameters
        ----------
            name (str): The name of the task to be called. Required

        """

        # if self.name is defined by a subclass, use it.
        if hasattr(self, 'name') and isinstance(self.name, str):
            if name is None:
                name = self.name
            # if name given is different from that defined in the class; fail
            if name != self.name:
                raise HSPTaskException(
                    f'given task name "{name}" does not ' +
                    f'match the name in the class "{self.name}"')
        # task name is required #
        if name is None:
            raise HSPTaskException('Task name is required')

        # to handle "_" and "-" in names, we also create pyname
        self.taskname = name
        self.pytaskname = name.replace('-', '_')

        # first read the parameter file
        pfile = HSPTask.find_pfile(name)
        params = HSPTask.read_pfile(pfile)

        # par_names: holds a list of the parameter names as strings
        # make each parameter accessible as: task.par_name
        par_names = []
        for par in params:
            setattr(self, par.pname, par)
            par_names.append(par.pname)

        # add extra useful keys to parameters
        default_mode = self.mode.value if hasattr(self, 'mode') else 'h'
        for pname in par_names:
            par = getattr(self, pname)
            if not hasattr(par, 'mode'):
                isReq = False
            else:
                isReq = ('q' in par.mode or
                         ('a' in par.mode and 'q' in default_mode))
            par.isReq = isReq

        self.par_names = par_names
        self.params = {}
        self.default_params = {
            pname: getattr(self, pname).value for pname in par_names}
        self.pfile = pfile
        self._task_docs = None
        self.__doc__ = self._generate_fcn_docs(fhelp=True)

    def __setattr__(self, pname, val):
        """Enable setting a parameter by setting HSPParam equal to some value.

        Doing it this way because for non-class attributes (task parameters
        that are defined in __init__ and not the in class), setting and getting
        them is not accessible for an class instance, unless we do it this way.

        Parameters
        ----------
        pname: str
            parameter name to be set
        val: str
            parameter value to set.

        """
        try:
            attrObj = super(HSPTask, self).__getattribute__(pname)
        except AttributeError:
            # setting for the first time
            super(HSPTask, self).__setattr__(pname, val)
        else:
            if hasattr(attrObj, '__set__'):
                attrObj.__set__(self, val)
                self.params[pname] = val
            else:
                super(HSPTask, self).__setattr__(pname, val)

    def __call__(self, args=None, **kwargs):
        """Call the task.

        There are several ways to call HSPTask:
        1: HSPTask(): required parameters will be queried as usually done with
            heasoft tasks.
        2: HSPTask(previousHSPTask): initialize from a previously defined
            HSPTask.
        3: HSPTask(argsDict): argsDict is a dict of input parameters.
        4: HSPTask(foo=bar, x=0): parameters are passed in the kwargs dict.


        Parameters
        ----------
        args: HSPTask or dict
            Task parameters as another HSPTask or dict

        Keywords
        --------
        individual task parameters given as: parameter=value.

        Additionally, the user may pass other arguments that are common between
        all tasks. These include:

        verbose: This can take several values. In all cases, the text printed
            by the task is captured, and returned in HSPResult.stdout/stderr.
            Additionally:
            - 0 (also False or 'no'): Just return the text, no progress
                printing.
            - 1 (also True or 'yes'): In addition to capturing and returning
                the text, task text will printed into the screen as the task
                runs.
            - 2: Similar to 1, but also prints the text to a log file.
            - 20: In addition to capturing and returning the text, log it
                to a file, but not to the screen.
                In both cases of 2 and 20, the default log file name is
                {taskname}.log. A logfile parameter can be passed to the task
                to override the file name.

        noprompt: Typically, HSPTask would check the input parameters and
            queries any missing ones. Some tasks (e.g. pipelines) can run by
            using default values. Setting `noprompt=True`, disables checking
            and querying the parameters. Default is False.

        stderr: If True, make stderr separate from stdout. The default
            is False, so stderr is written to stdout.

        Returns:
            HSPResult instance.
            e.g. HSPResult(ret_code, std_out, std_err, params, custom_dict)
        """

        # assemble the user input, if any, into a dict
        if args is None:
            user_pars = {}
        elif isinstance(args, dict):
            user_pars = dict(args)
        elif isinstance(args, HSPTask):
            user_pars = dict(args.params)
        else:
            raise HSPTaskException(
                'Unrecognized input in initializing HSPTask')

        # also any parameters in self.params from a previous call
        # or entered by hand
        user_pars.update(self.params)

        # add all keywords if present
        # any commandLine arguments in sys.argv should have already been
        # processed into kwargs
        user_pars.update(kwargs)

        # ----------------------------- #
        # handle common task parameters #
        # do we have an explicit stderr
        stderr = user_pars.get('stderr', False)
        if not isinstance(stderr, bool):
            stderr = ((isinstance(stderr, str) and
                       stderr.strip().lower() in ['y', 'yes', 'true'])
                      or isinstance(stderr, int) and stderr > 0)
        self.stderr = stderr

        # noprompt?
        noprompt = user_pars.get('noprompt', False)
        if 'noprompt' in self.par_names:
            # in case noprompt is task parameter, we look for py_noprompt
            noprompt = user_pars.get('py_noprompt', False)
        if not isinstance(stderr, bool):
            noprompt = ((isinstance(noprompt, str) and
                         noprompt.strip().lower() in ['y', 'yes', 'true'])
                        or isinstance(noprompt, int) and noprompt > 0)
        self._noprompt = noprompt

        # verbose?
        verbose = user_pars.get('verbose', 0)
        logfile = user_pars.get('logfile', None)
        if 'verbose' in self.par_names:
            # in case verbose is task parameter, we look for py_verbose
            verbose = user_pars.get('py_verbose', 0)
        if 'logfile' in self.par_names:
            # in case logfile is task parameter, we look for py_logfile
            logfile = user_pars.get('py_logfile', None)

        if isinstance(verbose, bool):
            verbose = 1 if verbose else 0
        elif isinstance(verbose, str):
            if verbose.strip().lower() in ['y', 'yes', 'true']:
                verbose = 1
            elif verbose.strip().lower() in ['n', 'no', 'false']:
                verbose = 0
            else:
                try:
                    verbose = int(verbose)
                except ValueError:
                    verbose = 1
        if not isinstance(verbose, int):
            raise HSPTaskException(
                'confusing verbose value. Allowed types are: bool, str or int')
        self._verbose = verbose
        # ----------------------------- #

        # prepare the logger #
        # note that verbose takes precedence over logfile
        if verbose <= 0:
            # capture only
            level = 1
            logfile = None
        elif verbose == 1:
            # capture & screen
            level = [1, 2]
            logfile = None
        elif verbose == 20:
            # capture and logfile
            level = [1, 3]
            if logfile is None:
                logfile = f'{self.taskname}.log'
        else:
            # capture, screen and logfile
            level = [1, 2, 3]
            if logfile is None:
                logfile = f'{self.taskname}.log'

        self._logfile = logfile

        # setup logger only for pure-python calls, not for native heasoft tools
        # those are handled separately by handle_io_stream
        if self.__module__ != 'heasoftpy.core':
            logging.setLoggerClass(HSPLogger)
            self.logger = logging.getLogger(self.taskname)
            self.logger.setup(
                level=level, stderr=self.stderr, file_name=logfile)
        # ------------------ #

        # now check the user input against expectations, and query if
        # incomplete
        usr_params = self.build_params(user_pars)

        # create a dict for all model parameters
        params = {p: getattr(self, p).value for p in self.par_names}
        self.params = usr_params if self._noprompt else params

        # do_exec is a hidden parameter used for debugging and testing
        # Set to True, unless we are testing and debugging.
        do_exec = kwargs.get('do_exec', True)
        if do_exec:
            # disable prompt:
            # https://heasarc.gsfc.nasa.gov/lheasoft/scripting.html
            os.environ['HEADASNOQUERY'] = ''
            os.environ['HEADASPROMPT'] = '/dev/null'

            # write new params to the user .par file
            # do this before calling in case the task also updates
            # the .par file
            usr_pfile = HSPTask.find_pfile(self.taskname, return_user=True)
            self.write_pfile(usr_pfile)

            # now call the task #
            result = self.exec_task()

            # ensure we are returning the correct type
            if not isinstance(result, HSPResult):
                raise HSPTaskException(
                    f'Returned result type {type(result)} is not HSPResult')

            # re-read the pfile in case it has been modified by the task
            # update only the the values in the HSPTask instance, not
            #  result.params that will be returned to the user
            if os.path.exists(usr_pfile):
                params_after = HSPTask.read_pfile(usr_pfile)
                for ipar, par_name in enumerate(self.par_names):
                    setattr(self, par_name, params_after[ipar].value)
                # result.params.update(self.params)

            return result

    def exec_task(self):
        """Run the Heasoft task. This is not meant to be called directly.

        This method can be overridden by python-only tasks that subclass
        HSPTask. The task parameters are available as dictionary of
        {par_name:value} that contain both the parameters passed by the
        user and default ones.

        Here, we just call the heasoft task as a subprocess


        Returns
        -------
        HSPResult instance.
            e.g. HSPResult(ret_code, std_out, std_err, params, custom_dict)

        """

        # Get the task parameters
        usr_params = self.params

        verbose = self._verbose

        # do we have stderr?
        stderr = subprocess.PIPE if self.stderr else subprocess.STDOUT

        # construct a parameter list
        for par in usr_params.keys():
            if isinstance(usr_params[par], bool):
                usr_params[par] = 'yes' if usr_params[par] else 'no'
            if usr_params[par] is None:
                usr_params[par] = 'NONE'

            if isinstance(usr_params[par], str):
                # '$( )' ensures empty string are passed correctly with
                # subprocess
                if usr_params[par] == '':
                    usr_params[par] = '$( )'
        cmd_params = [
            '{}={}'.format(par, val) for par, val in usr_params.items()]

        # the task executable
        exec_cmd = os.path.join(os.environ['HEADAS'], f'bin/{self.taskname}')

        if os.path.exists(exec_cmd):
            exec_cmd = [exec_cmd]
        elif os.path.exists(exec_cmd + '.py'):
            exec_cmd = ['python', exec_cmd + '.py']
        else:
            raise HSPTaskException(f'There is no task file {exec_cmd} to run')

        cmd_list = exec_cmd + cmd_params
        proc = subprocess.Popen(cmd_list, stdout=subprocess.PIPE,
                                stderr=stderr, env=os.environ.copy())

        # ---------------------------------------------------- #
        # if verbose, we need to both print and capture output #
        # keeping track of stdout and stderr                   #
        # pass this to handle_io_stream to deal with it        #
        # ---------------------------------------------------- #
        if verbose > 0:
            proc_out, proc_err = HSPTask.handle_io_stream(
                proc, self.stderr, verbose, self._logfile)
            # needed to ensure the returncode is set correctly
            proc.wait()
        else:
            proc_out, proc_err = proc.communicate()
            if isinstance(proc_out, bytes):
                proc_out = proc_out.decode('ISO-8859-15')
            if isinstance(proc_err, bytes):
                proc_err = proc_err.decode('ISO-8859-15')
        # ---------------------------------------------------- #

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
        if self._task_docs is not None:
            return self._task_docs

        name = self.taskname

        # call fhelp; assume HEADAS is defined #
        hbin = f"{os.environ['HEADAS']}/bin"
        fhelp = f"{hbin}/fhelp"

        if os.path.exists(f'{hbin}/{name}'):
            ext = ''
        elif os.path.exists(f'{hbin}/{name}.py'):
            ext = '.py'
        else:
            ext = None

        if ext is None:
            fhelp = f'Cannot run fhelp for {name}. No fhelp text was generated'
        else:
            proc = subprocess.Popen(
                [fhelp, f'task={name}{ext}'], stdin=subprocess.PIPE,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            proc_out, proc_err = proc.communicate()
            fhelp = proc_out.decode('ISO-8859-15')
            fhelp = f"{'-'*50}\n   fhelp-generated text\n{'-'*50}\n{fhelp}"
            fhelp.replace('"""', '')
            # add tab to the fhelp text
            fhelp = ''.join([line if line == '\n' else
                             f'    {line}' for line in fhelp.splitlines(True)])
        # ------------------------------------- #
        self._task_docs = fhelp
        return fhelp

    def build_params(self, user_pars):
        """Check the parameters given by the user against expectation
        from the .par file.

        - Loop through the expected task parameters (self.all_params).
        - Update their value if any of them is given by the user (in user_pars)
        - if a parameter is required by the task and not given, query the user.
        The final updated list of parameters is returned

        Parameters
        ----------
        user_pars: dict
            a dictionary containing the par_name:value given by the user

        Return
        ------
        dict of {pname:pvalue} for the values either passed by user or queried
        if required
        """

        # ----------------------------------------------------------- #
        # handle relation between parameters. these are task-specific
        # and need to be done in a better way

        # if page==no, do not query for more, regardless
        page = self.page if 'page' in self.par_names else None
        upage = user_pars.get('page', None)
        if page is not None:
            if self.page.value == 'no' or upage == 'no':
                user_pars['more'] = 'yes'

        noprompt = self._noprompt
        # ----------------------------------------------------------- #

        # do some basic checks on user_pars #
        # some heasoft tasks don't handle quotes in comma-separated lists
        # correctly
        for par in user_pars.keys():
            if isinstance(user_pars[par], str) and ',' in user_pars[par]:
                user_pars[par] = user_pars[par].strip('"')
        # --------------------------------- ##

        # loop through task parameters and either:
        params = {}
        # for pname, pdesc in self.all_params.items():
        for par_name in self.par_names:
            par = getattr(self, par_name)
            isReq = par.isReq

            if par_name in user_pars:
                setattr(self, par_name, user_pars[par_name])
                params[par_name] = par.value

            elif isReq and not noprompt:
                # query parameter
                par.query()
                params[par_name] = par.value
            else:
                # parameter not needed and not given
                pass
        return params

    def write_pfile(self, pfile):
        """Write .par file of some task, typically after executing

        Parameters
        ----------
        pfile: str
            path and name of the .par file. If it doesn't exist, create it

        Return:
            None

        """

        # write the updated parameter list #
        defaults = self.default_params
        ptxt = ''
        for par_name in self.par_names:
            par = getattr(self, par_name)

            val = par.value
            if (
                par.mode in ['h', 'q'] or
                (par.mode == 'a' and 'l' not in defaults['mode'])
            ):
                val = defaults[par_name]

            # make any style changes to the values to be printed #
            if (par.type in ['s', 'f', 'fr'] and isinstance(val, str) and
                    (' ' in val or ',' in val or val == '')):
                val = f'"{val}"'

            # write #
            ptxt += (f'{par.pname},{par.type},{par.mode},' +
                     f'{val},{par.min},{par.max},\"{par.prompt}\"\n')

        with open(pfile, 'w') as pf:
            pf.write(ptxt)
        # -------------------------------- #

    @staticmethod
    def read_pfile(pfile):
        """Read a par file for some task

        Can be called without initializing HSPTask by doing:
        HSPTask.read_pfile(...)

        Parameters
        ----------
        pfile: str
            full path to .par file

        Returns:
            list of HSPParam instances

        """

        if not os.path.exists(pfile):
            raise IOError(f'parameter file {pfile} not found')

        params = []
        with open(pfile, 'r') as fp:
            for line in fp:

                # make sure we have a line with information
                if line.startswith('#') or len(line.split(',')) < 6:
                    continue

                params.append(HSPParam(line))

        # if no mode, assume ql
        if 'mode' not in [par.pname for par in params]:
            params.append(HSPParam('mode,s,h,ql,,,'))

        return params

    @staticmethod
    def find_pfile(name, return_user=False):
        """Search for an return the .par file for the task

        Parameters
        ----------
        name: str
            Name of the task, so the pfile is {name}.par
        return_user: bool
            return the user pfile, even if it doesn't exist
            User's pfile is the taken from the first entry to PFILES

        Returns:
            the path to the {name}.par pfile

        """

        if 'HEADAS' in os.environ:
            sys_pfile = os.path.join(
                os.environ['HEADAS'], 'syspfiles', f'{name}.par')
        else:
            raise HSPTaskException(
                'HEADAS not defined. Please initialize Heasoft!')

        # during installation, always use $HEADAS/syspfiles
        if ('__INSTALLING_HSP' in os.environ and
           os.environ['__INSTALLING_HSP'] == 'yes'):
            return sys_pfile

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

        # parameter file to read
        pfile_to_read = os.path.join(pf, f'{name}.par')

        # check time-stamps; if we have a fresh heasoft or fresh heasoftpy
        # always read from sys_pfile
        this_ts = os.path.getmtime(__file__)
        sys_ts = (os.path.getmtime(sys_pfile)
                  if os.path.exists(sys_pfile) else -1.0)
        pfile_ts = (os.path.getmtime(pfile_to_read)
                    if os.path.exists(pfile_to_read) else -1.0)
        if (sys_ts >= pfile_ts or this_ts >= pfile_ts) and not return_user:
            return sys_pfile

        # parameter file where to save the task parameters
        if pfiles[0] == sys_pfile:
            # use ~/pfiles
            out_pdir = os.path.expanduser('~/pfiles')
        else:
            # use the first entry (other than sys_pfile) in PFILES
            out_pdir = pfiles[0]

        if not os.path.isdir(out_pdir):
            os.mkdir(out_pdir)
        pfile_to_write = f'{out_pdir}/{name}.par'

        # if return_user, we should never return sys_pfile because,
        # now we preparing to write
        pfile = pfile_to_write if return_user else pfile_to_read
        return pfile

    @staticmethod
    def handle_io_stream(proc, stderr, verbose, logfile):
        """Internal method to handle multiple streams (file & screen)

        Parameters:
            proc:
                proc from subprocess or sys; i.e. it has proc.stdout
                and proc.stderr
            stderr: bool
                user input of whether to use stderr or not

        """
        # selectors handle multiple io streams
        # https://stackoverflow.com/questions/31833897/python-read-from-subprocess-stdout-and-stderr-separately-while-preserving-order
        selector = selectors.DefaultSelector()
        selector.register(proc.stdout, selectors.EVENT_READ)
        outBuf = io.StringIO()
        if stderr:
            selector.register(proc.stderr, selectors.EVENT_READ)
            errBuf = io.StringIO()
        file = None
        if logfile is not None:
            file = open(logfile, 'a')

        # while task is running, print/capture output #
        done = False
        while not done:
            for key, _ in selector.select():
                line = key.fileobj.read1().decode()
                if not line:
                    done = True
                if not stderr or key.fileobj is proc.stdout:
                    if verbose != 20:
                        sys.stdout.write(line)
                    outBuf.write(line)
                    if file:
                        file.write(line)
                else:
                    if verbose != 20:
                        sys.stderr.write(line)
                    errBuf.write(line)
                    if file:
                        file.write(line)
        proc_out = outBuf.getvalue()
        outBuf.close()
        proc_err = None
        if stderr:
            proc_err = errBuf.getvalue()
            errBuf.close()
        if file:
            file.close()
        return proc_out, proc_err

    def _generate_fcn_docs(self, fhelp=False):
        """Generation standard function docstring from .par file


        Parameters
        ----------
        fhelp: bool
            If True, call task_docs to generate standard help with fhelp

        Return
        ------
        str containing the help docs.

        """
        # parameter description #
        parsDesc = ''
        for par_name in self.par_names:
            par = getattr(self, par_name)
            parsDesc += (
                f'\n    {par.pname:12} {"(Req)" if par.isReq else "":6}:')
            parsDesc += f'  {par.prompt} (default: {par.default}) '
        # --------------------- #

        # get extra docs from the task #
        # do this only if fhelp is True; i.e. genearating wrappers
        task_docs = self.task_docs() if fhelp else ''

        # put it all together #
        docs = (
            f'    \n\n'
            '    Parameters\n    ----------'
            f'{parsDesc}\n\n{task_docs}'
        )

        return docs

    def generate_fcn_code(self, deprecate_text=None):
        """Create python function for task_name

        """
        task_name = self.taskname
        task_pyname = self.pytaskname

        # generate docstring
        docs = self._generate_fcn_docs(fhelp=True)

        # do we have a depratation text
        depr_import, depr_text = '', ''
        if deprecate_text is not None:
            depr_import = 'from astropy.utils.decorators import deprecated\n'
            depr_import += 'from ..core import HSPDeprecationWarning\n'
            depr_text = deprecate_text

        # generate function text
        fcn = (
            '# Copyright 2023, University of Maryland, All Rights Reserved\n\n'
            f'{depr_import}\n'
            'from ..core import HSPTask, HSPTaskException\n\n\n'
            f'{depr_text}\n'
            f'def {task_pyname}(args=None, **kwargs):\n'
            f'    r"""\n{docs}\n    """\n\n'
            f'    {task_pyname}_task = HSPTask(name="{task_name}")\n'
            f'    return {task_pyname}_task(args, **kwargs)\n'
        )
        return fcn


class HSPResult:
    """Container for the result of a task execution"""

    def __init__(self, returncode, stdout, stderr=None, params=None,
                 custom=None):
        """Create a result object to summarize the return of a task


        Args:
            ret_code: return code from running the task
            std_out: The returned string in standard output
            std_err: The returned standard error, or None
            params: a dict containing the task parameters
            custom: a dict of any extra parameters.

        """

        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        self.params = dict(params) if isinstance(params, dict) else params
        self.custom = dict(custom) if isinstance(custom, dict) else custom

    def __str__(self):
        """Print the result object in a clean way"""

        txt = ('-'*21) + '\n:: Execution Result ::\n' + ('-'*21)
        txt += f'\n> Return Code: {self.returncode}'
        txt += f'\n> Output:\n{self.stdout}'
        if self.stderr is not None:
            txt += f'\n> Errors: {self.stderr}'
        ptxt = '\n\t'.join([f'{par:10}: {val}'
                            for par, val in self.params.items()])
        txt += f'\n> Parameters:\n\t{ptxt}'
        return txt

    def __repr__(self):
        return self.__str__()

    @property
    def output(self):
        """Return the standard output as a list of line"""
        return self.stdout.split('\n')


class HSPParam():
    """Class for holding task parameters """

    def __init__(self, line):
        """Initialize a parameter object with a line from the .par file

        Parameters
        ----------
        line: str
            a line from the parameter file

        """
        line = line.replace('\n', '')
        # if there is an unclosed "|' in the prompt.
        # This should be fixed in the file
        # but we add it here for generality
        if line.count('"') % 2 != 0:
            line += '"'
        # unclosed (') is fine, e.g. "file's name"; so we close
        # it, then remove it later
        sgl_quote = False
        if line.count("'") % 2 != 0:
            line += "'"
            sgl_quote = True

        # split at ,
        info = line.strip().split(',')

        # handle characters (,"') in the prompt text
        if len(info) > 7:
            # - split the line so closed strings (with ' or ") are in
            # separate parts
            parts = re.split("('.*?'|\\\".*?\\\")", line)

            # if any value or prompt contains ",", replace it with "^|_",
            # split, then put it back. Assumes "^|_" is not going to appear
            # anywhere
            # - replace (,) with (^|_) if , falls in one of the substrings
            # with (',")
            parts = [
                p.replace(',', '^|_') if ('"' in p or "'" in p) else p.strip()
                for p in parts]
            # - put things back together, and then split at , and remove ^|_
            info = [p.replace('^|_', ',').strip()
                    for p in ''.join(parts).split(',')]

        # assume all text at the end is part of the prompt
        if len(info) > 7:
            info[6] = ', '.join(info[6:])
            info = info[:7]

        # extract information about the parameter
        self.pname = info[0].strip()
        pkeys = ['type', 'mode', 'default', 'min', 'max', 'prompt']
        for ikey, key in enumerate(pkeys):
            setattr(self, key, info[ikey+1].strip().strip('"'))

        # handle case of single quote like: prompt="file's name"
        if sgl_quote and self.prompt.split("'")[-2][0] == 's':
            setattr(self, 'prompt', self.prompt[:-1])

        self.default = HSPParam.param_type(self.default, self.type)
        self.value = self.default

    def __set__(self, obj, new_value):
        if obj is None:
            obj = self
        self.value = HSPParam.param_type(new_value, self.type)

    def __repr__(self):
        return f'param:{self.pname}:{self.value}'

    def __eq__(self, other):
        """When is a HSPParam equal to another"""
        if isinstance(other, HSPParam):
            return self.value == other.value
        else:
            return self.value == other

    def query(self):
        """Query the user for a parameter and set its value to self.value

        TODO: handle nan, None, INDEF etc

        """
        # querymsg = f':: {self.pname} ::\n{self.prompt} ({self.value}) > '
        querymsg = f'{self.prompt} [{self.value}] '
        done = False
        while not done:

            user_inp = input(querymsg)

            # special cases
            if user_inp == '':
                user_inp = self.value
            if self.type == 'b':
                user_inp = ('no' if user_inp.lower() in
                            ['n', 'no', 'false'] else 'yes')

            try:
                self.value = HSPParam.param_type(user_inp, self.type)
                done = True
            except ValueError:
                print(f'value {user_inp} cannot be processed. Try again!')

    @staticmethod
    def param_type(value, inType):
        """Find the correct type from pfiles

        Parameters
        ----------
        value: str (or possibly int or float)
            The value to be converted; typically a str
        inType: str
            a str representing the type in the .par files.
            One of: {i, s, f, b, r, fr, b}

        Returns:
            the value in the correct type

        """

        # handle special cases first
        if not isinstance(value, str):
            # already done
            return value

        if value == 'INDEF' and inType in ['r', 'i']:
            return value

        if value == '' and inType in ['r', 'i']:
            value = 0

        if inType == 'b':
            value = 1 if value.lower() in ['y', 'yes', 'true'] else 0

        if inType in ['r', 'i']:
            value = str(value).replace("'", "").replace('"', '')

        # now proceed with the conversion
        switcher = {'i': int, 's': str, 'f': str, 'b': bool,
                    'r': float, 'fr': str, 'd': str, 'g': str, 'fw': str}

        if inType not in switcher.keys():
            raise ValueError(f'parameter type {inType} is not recognized.')

        # TODO: more error trapping here
        result = switcher[inType](value)

        # keep boolean as yes/no not True/False
        if inType == 'b':
            result = 'yes' if result else 'no'
        return result


class HSPLogger(logging.getLoggerClass()):
    """A logger for the tasks.
    The same as the main logger in logging, but we add a setup
    method to setup the handlers, and an output attribute to return
    the string captured.

    """

    def __init__(self, name):
        """initialize by calling the parent initializer"""
        self.name = name
        super().__init__(name)
        self.isSetup = False

    def setup(self, **kwargs):
        """Setup the logger by:
        - creating a string stream for all levels to capture output
        - creating a string stream for errors if stderr=True
        - creating a console stream if level 2 is requested
        - creating a file stream if level 3 is request. This prints
            more debugging details


        Keyword Args:
            level: 1: basic, 2: short, 3: long. This should an integer
                or a list of integers, if different levels are considered
            file_name: file name to use when level==3. Default is {name}.log
            stderr: pipe errors to a separate stream. Default is False, so
                errors are written to stdout
        """

        # inputs are in keywords #
        level = kwargs.get('level', 1)
        file_name = kwargs.get('file_name', None)
        self.stderr = kwargs.get('stderr', False)

        # setup only once: #
        if self.isSetup:
            # only clean the streams
            self.oStream = io.StringIO()
            if self.stderr:
                self.eStream = io.StringIO()
        self.isSetup = True
        if file_name is not None and os.path.exists(file_name):
            os.remove(file_name)
        # ---------------- #

        # check the values of level
        if not isinstance(level, (int, list)):
            raise ValueError('level should be int or a list')
        if isinstance(level, int):
            level = [level]

        # starting level
        self.setLevel(logging.DEBUG)

        # Stream to capture the output
        self.oStream = io.StringIO()
        if self.stderr:
            self.eStream = io.StringIO()

        # filters to handle errors separately if needed
        def error_filter(record):
            return record.levelname in ['ERROR', 'CRITICAL']

        def noerror_filter(record):
            return not error_filter(record)

        # handlers:
        if 1 in level:
            # Stream to a string
            handler = logging.StreamHandler(self.oStream)
            handler.setLevel(logging.INFO)
            handler.setFormatter(logging.Formatter('%(message)s'))
            if self.stderr:
                handler.addFilter(noerror_filter)

                # add an error-only handler #
                ehandler = logging.StreamHandler(self.eStream)
                ehandler.setLevel(logging.DEBUG)
                ehandler.setFormatter(logging.Formatter('%(message)s'))
                ehandler.addFilter(error_filter)
                self.logger.addHandler(ehandler)

            self.addHandler(handler)

        if 2 in level:
            # Console handler to print progress
            handler = logging.StreamHandler()
            handler.setLevel(logging.INFO)
            handler.setFormatter(logging.Formatter('%(message)s'))
            self.addHandler(handler)

        if 3 in level:
            # print progress to a file
            handler = logging.FileHandler(file_name, mode='a')
            handler.setLevel(logging.DEBUG)
            handler.setFormatter(
                logging.Formatter(('%(asctime)s|%(levelname)5s|%(filename)s|'
                                  '%(funcName)s|%(message)s'))
            )
            self.addHandler(handler)

    @property
    def output(self):
        """Return the content captured in the log stream, and flush it"""
        out = self.oStream.getvalue()
        self.oStream = io.StringIO()
        err = None
        if self.stderr:
            err = self.eStream.getvalue()
            self.eStream = io.StringIO()
        self.isSetup = False

        return out, err
