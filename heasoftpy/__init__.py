# Copyright 2024, University of Maryland, All Rights Reserved
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
python (versions later than 3.8)
astropy


EXAMPLES:
--------------
Tasks in heasoftpy can be used in different ways.

- Built-in tasks can be called directly:
>>> result = hsp.ftlist(infile='input.fits', option='T')


- A task object can be created and called (even if not installed in heasoftpy):
>>> ftlist = hsp.HSPTask('ftlist')
>>> result = ftlist(infile='input.fits', option='T')


The input to the functions is also flexible:

- Use individual parameters:
>>> result = hsp.ftlist(infile='input.fits', option='T')

- Pass a dictionary of parameters:
>>> params = {'infile':'input.fits', 'option':'T'}
>>> result = hsp.ftlist(params)

- When using HSPTask, the task parameters can also be input inline as task
attributes:
>>> ftlist = hsp.HSPTask('ftlist')
>>> ftlist.infile = 'input.fits'
>>> ftlist.option = 'T'
>>> result = ftlist()


All tasks take additional optional parameters:
- verbose: This can take several values. In all cases, the text printed by the
    task is captured, and returned in HSPResult.stdout/stderr. Additionally:
    - 0 (also False or 'no'): Just return the text, no progress printing.
    - 1 (also True or 'yes'): In addition to capturing and returning the text,
        task text will printed into the screen as the task runs.
    - 2: Similar to 1, but also prints the text to a log file.
    - 20: In addition to capturing and returning the text, log it to a file,
        but not to the screen.
        In both cases of 2 and 20, the default log file name is {taskname}.log.
        A logfile parameter can be passed to the task to override the file
        name.
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
from .core import HSPTask, HSPTaskException  # noqa 401
from . import utils  # noqa 401


# help function
def help(): print(__doc__)


# version
from .version import __version__  # noqa 401


# a helper function to check a package exists
def _package_exists(package):
    thisdir = os.path.dirname(__file__)
    return os.path.exists(os.path.join(thisdir, package))


# load sub-packages, only if we are not installing the main package:
# __INSTALLING_HSP is created in install.py during installation
if '__INSTALLING_HSP' not in os.environ:
    # import the core heasoft tools
    # Temporary for Old compatibility ##
    # delete once fcn is removed      ##
    from .fcn import *  # noqa 401
    if _package_exists('ixpe'):
        from ._ixpe import *  # noqa 401
    # ------------------------------- ##
    from .heacore import *  # noqa 401

    # the following are not always installed
    try:
        from .ftools import *  # noqa 401
    except ImportError:
        pass
    try:
        from .heagen import *  # noqa 401
    except ImportError:
        pass
    try:
        from .heasim import *  # noqa 401
    except ImportError:
        pass
    try:
        from .heasptools import *  # noqa 401
    except ImportError:
        pass
    try:
        from .attitude import *  # noqa 401
    except ImportError:
        pass
    try:
        from .Xspec import *  # noqa 401
    except ImportError:
        pass
    try:
        from .heatools import *  # noqa 401
    except ImportError:
        pass
