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


All tasks take additional optional parameters:
- verbose: If True, print the task output to screen. Default is False
- noprompt: Typically, HSPTask would check the input parameters and 
    queries any missing ones. Some tasks (e.g. pipelines) can run by using
    default values. Setting noprompt=True, disables checking and quering 
    the parameters. Default is False.
- stderr: If True, make stderr separate from stdout. The default
    is False, so stderr is written to stdout.



HELP:
----
Help for tasks can be accesed by:
>>> hsp.fdump?


ADDIING PYTHON TASKS
--------------------
The core of HEASoftpy os the class HSPTask, which handles the .par 
parameter reading and setting. It was written in a way to make it 
easy for writing new codes that can be easily integrated within 
HEASoft. All that is needed, in addition to creating a .par file, 
is to create subclass of HSPTask and implements a method exec_task 
that does the task function. 

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
from .core import HSPTask, HSPTaskException, HSPResult, HSPParam
from . import utils

from .fcn import *

# help function
def help(): return print(__doc__)

# version
from .version import __version__