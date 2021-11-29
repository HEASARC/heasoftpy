Python interface to HeaSoft
===========================

## Content
- [About](#about)
- [Usage](#usage)
- [Installation](#installation)
- [Writing Python Tasks](#writing-Python-Tasks)


## About:
`HEASoftpy` is a Python 3 package that gives access to the `HEASoft` 
tools using python. It provies python wrappers that call the 
`HEASoft` tools, allowing for easy integration into other python
code.

`HEASoftpy` also provides the framework that allows for pure-python
tools to be integrated within the `HEASoft` system.

Although `HEASoftpy` is written in pure python, it does NOT rewrite 
the functions and tools already existing in `HEASoft`. A working
installation of `HEASoft` is therefore required.


## Usage
After intallation (see [installation](#installation)), `HEASoftpy` can
be used is several ways.

### Different way of usage:
1- Importing the task methods:
```python

import heasofpy as hsp
hsp.fdump(infile='input.fits', outfile='STDOUT', ...)

```

2- Creating a `HSPTask` and invoking it:
```python

import heasofpy as hsp
fdump = hsp.HSPTask('fdump')
fdump(infile='input.fits', outfile='STDOUT', ...)

```

3- Using it directly from the command line, similar to the standard `HEASoft` tools:
```bash

fdump.py infile=input.fits outfile=STDOUT ...

```

### Different ways to pass parameters:
Additionally, the task methods handle different types in inputs. For example:

```python

import heasofpy as hsp
hsp.fdump(infile='input.fits', outfile='STDOUT', ...)

# or
params = {
    'infile': 'input.fits',
    'outfile': 'STDOUT',
    ...
}
hsp.fdump(params)

# or
fdump_task = hsp.HSPTask('fdump')
fdump_task(infile='input2.fits', outfile='STDOUT', ...)
hsp.fdump(fdump_task)

# or
fdump_task = hsp.HSPTask('fdump')
fdump_task.infile = 'input2.fits'
fdump_task.outfile = 'STDOUT'

# or a combination of the above

```

Whenver a task in called, if any of the required parameters is missing, 
the user is prompted to enter a value.

Note that ceatting a task object with `fdump_task = hsp.HSPTask('fdump')` does
not actually call the task. Only doing `fdump_task(...)` that it is called and 
paramters are queried if necessary.


### Common `heasoftpy` Parameters:
There are a few parameters that can be used by all tasks:
- verbose: If True, print the task output to screen. Default is False
- noprompt: Typically, HSPTask would check the input parameters and 
    queries any missing ones. Some tasks (e.g. pipelines) can run by using
    default values. Setting noprompt=True, disables checking and quering 
    the parameters. Default is False.
- stderr: If True, make stderr separate from stdout. The default
    is False, so stderr is written to stdout.


### Finding help for the tasks
The help for the tasks can be accessed in the standard python way.
```python
hsp.fdump?
```

which will print something like the following, indicating the required parameters:
```
    Automatically generated function for Heasoft task fdump.
    Additional help may be provided below.

    Args:
     infile       (Req) : Name of FITS file and [ext#] (default: test.fits)
     outfile      (Req) : Name of optional output file (default: STDOUT)
     columns      (Req) : Names of columns (default: -)
     rows         (Req) : Lists of rows (default: -)
     fldsep             : Define a new field separator (default is space) (default: )
     pagewidth          : Page width (default: 80)
     prhead             : Print header keywords? (default: True)
     prdata             : Print data? (default: True)
     showcol            : Print column names? (default: True)
     showunit           : Print column units? (default: True)
     showrow            : Print row numbers? (default: True)
     showscale          : Show scaled values? (default: True)
     align              : Align columns with names? (default: True)
     skip               : Print every nth row (default: 1)
     tdisp              : Use TDISPn keywords? (default: False)
     wrap               : Display entire row at once? (default: False)
     page               : Page through output to terminal (default: True)
     clobber            : Overwrite output file if exists? (default: False)
     sensecase          : Be case sensitive about column names? (default: False)
     xdisp              : How to display nX Column(default/(b or B)/(D or d)? (default: )
     more         (Req) : More? (default: yes)
     mode               :  (default: ql)

...
```
Scrolling down further, the help message will print the standard HEASoft help text from `fhelp`.
```
--------------------------------------------------
   The following has been generated from fhelp
--------------------------------------------------
NAME

   fdump -- Convert the contents of a FITS table to ASCII format.

USAGE

        fdump infile[ext#] outfile columns rows

DESCRIPTION

   This task converts the information in the header and data of a FITS
   table extension (either ASCII or binary table) ...
   
```


## Installation
TODO

---
## Writing Python Tasks
The core of `HEASoftpy` os the class `HSPTask`, which handles the `.par` parameter reading and setting.

It was written in a way to make it easy for writing new codes that can be easily integrated within `HEASoft`. All that is needed, in addition to creating a `.par` file, is to create subclass of `HSPTask` and implements a method `exec_task` that does the task function. An example is given in `contrib/sample.py`. The following is short snippet:

```python

import heasoftpy as hsp

class SampleTask(hsp.HSPTask):
    """New Task"""
    
    def def exec_task(self):
        
        # model parameters
        usr_params = self.params
        
        # write your task code here #
        # ...
        # ...
        # ------------------------- #
        
        # finally return a HSPResult
        return hsp.HSPResult(0, out, None, usr_params)
        
```
The `HSPTask` class provides two variables that hold the parameters:
- `usr_params`: is a dict for the task parameters

`HSPResult` is a simple container of the task output, which contains:
- `returncode`: a return code: 0 if the task executed smoothly (int).
- `stdout`: standard output (str).
- `stderr`: standard error message (str).
- `params`: dict of user parameters in case the task changed them, used to update the .par file.
- `custom`: dict of any other variables to returned by the task.

You can also define a method `task_docs` in `SampleTask` that returns a string of the documentations of the task. This will be appended to the docstring automatically generated from the `.par` parameter. For example:

```python

    def task_docs(self):
        docs = "*** Documentation for the sample code goes here! ***"
        return docs
```