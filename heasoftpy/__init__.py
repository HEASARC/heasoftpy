"""

DESCRIPTION:
-----------
HEASoftpy is a Python package to wrap the HEASoft tools so that
they can be called from python scripts, interactive ipython 
sessions, or Jupyter Notebooks.  

>>> import heasoftpy as hsp
>>> help(hsp.fdump)
...

>>> result = hsp.ftlist(infile='input.fits', option='T')
>>> print(result.stdout)
...

REQUIREMENTS:
--------------
python (versions later than 3.7)
astropy


EXAMPLE USAGE:
--------------
Using tasks in heasoftpy offer flexibility in usage.

- Built-in tasks can be called directly (if installed in heasoftpy/fcn):
>>> result = hsp.ftlist(infile='input.fits', option='T')


- A task object can be created and called (even if not installed in heasoftpy/fcn):
>>> ftlist = hsp.HSPTask('ftlist')
>>> result = ftlist(infile='input.fits', option='T')


The input to the functions is also flexible:

- Use individual parameters:
>>> result = hsp.ftlist(infile='input.fits', option='T')

- Pass a dictionary of parameters:
>>> params = {'infile':'input.fits', 'option':'T'}
>>> result = hsp.ftlist(params)

- When using HSPTask, the task parameters can also be input inline as task attributes:
>>> ftlist = hsp.HSPTask('ftlist')
>>> ftlist.infile = 'input.fits'
>>> ftlist.option = 'T'
>>> result = ftlist()


All tasks take additional optional parameters:
- verbose: This can take several values. In all cases, the text printed by the
    task is captured, and returned in HSPResult.stdout/stderr. Addionally:
    - 0 (also False or 'no'): Just return the text, no progress prining.
    - 1 (also True or 'yes'): In addition to capturing and returning the text,
        task text will printed into the screen as the task runs.
    - 2: Similar to 1, but also prints the text to a log file.
    - 20: In addition to capturing and returning the text, log it to a file, 
        but not to the screen. 
        In both cases of 2 and 20, the default log file name is {taskname}.log. 
        A logfile parameter can be passed to the task to override the file name.
- noprompt: Typically, HSPTask would check the input parameters and 
    queries any missing ones. Some tasks (e.g. pipelines) can run by using
    default values. Setting noprompt=True, disables checking and querying 
    the parameters. Default is False.
- stderr: If True, make `stderr` separate from `stdout`. The default
    is False, so stderr is written to stdout.




HELP:
----
Help for tasks can be accessed by:
>>> hsp.fdump?


ADDIING PYTHON TASKS
--------------------
The core of HEASoftpy is the HSPTask class, which handles the
parameter reading from the parameter files and parameter setting.
This class makes it easier to integrate new code within
HEASoft. To create a new task, all that is needed is to create a .par file in the user's
PFILES directory (usually $HOME/pfiles) and to create subclass of HSPTask
and implement a method called exec_task that performs the desired task function.

For example

>>> class SampleTask(hsp.HSPTask):
>>>     def exec_task(self):
>>>        params = self.params
>>>        # --- write your code here --- #
>>>        # ...
>>>        # ---------------------------- #
>>>        return hsp.RSPResult(returncode, stdout, stderr, params)


NOTES:
------
Although HEASoftpy is written in pure python, it does NOT rewrite
the functions and tools already existing in HEASoft. A working
installation of HEASoft is therefore required.

"""
import os
from .core import HSPTask, HSPTaskException, HSPResult, HSPParam, HSPLogger
from . import utils

from .fcn import *

# help function
def help(): print(__doc__)

# version
from .version import __version__


# a helper function to check a package exists
def _package_exists(package):
    thisdir = os.path.dirname(__file__)
    return os.path.exists(os.path.join(thisdir, package))


# load sub-packages, only if we are not installing the main package:
# __INSTALLING_HSP is created in install.py during installation
if not '__INSTALLING_HSP' in os.environ:
    
    # if _package_exists('template'):
    #     import template
    #     from template import *

    # the following fixes any version discrepency between
    # cfitsio used in pyxspec and cfitsio used in astropy
    # which is needed by ixpe.
    # If xspec is imported *after* heasoftpy, and there is a 
    # cfitsio version discrepency, xspec may fail, but it appears
    # to work fine when importe before heasoftpy (ixpe in this case)
    try:
        import xspec as pyxspec
    except ImportError:
        pass
    
    if _package_exists('ixpe'):
        from . import ixpe
        from .ixpe import *
