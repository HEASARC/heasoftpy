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

- Built-in tasks can be called directly:
>>> result = hsp.ftlist(infile='input.fits', option='T')


- A task object can be created and called:
>>> ftlist = hsp.HSPTask('ftlist')
>>> result = ftlist(infile='input.fits', option='T')


- Or the python scripts can be called directly from the command Line:
>>> ftlist.py infile=input.fits option=T


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
- verbose: If True, print the task output to screen. Default is False
- noprompt: Typically, HSPTask would check the input parameters and 
    queries any missing ones. Some tasks (e.g. pipelines) can run by using
    default values. Setting noprompt=True, disables checking and querying
    the parameters. Default is False.
- stderr: If True, make stderr separate from stdout. The default
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
def help(): return print(__doc__)

# version
from .version import __version__

# load sub-packages, only if we are not installing the main package:
# __INSTALLING_HSP is created in install.py during installation
if not '__INSTALLING_HSP' in os.environ:
    
    from .packages.template import *
