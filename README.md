Python interface to HeaSoft
===========================

## Content
- [1. About](#1-about)
- [2. Usage](#2-usage)
    - [2.1 Different Ways of Calling the Tasks](#21-different-ways-of-calling-the-tasks)
    - [2.2 Different Ways of Passing Parameters](#22-different-ways-of-passing-parameters)
    - [2.3 Common `HEASoftpy` Parameters](#23-common-heasoftpy-parameters)
    - [2.4 Finding Help for the Tasks](#24-finding-help-for-the-tasks)
- [3. Installation](#3-installation)
- [4. Writing Python Tasks](#4-writing-python-tasks)
- [5. User Guide and Other Tutorials](#5-tutorials)


## 1. About:
`HEASoftpy` is a Python 3 package that gives access to the `HEASoft` 
tools using python. It provies python wrappers that call the 
`HEASoft` tools, allowing for easy integration into other python
code.

`HEASoftpy` also provides a framework that allows for pure-python
tools to be developed and integrated within the `HEASoft` system (see [Writing Python Tasks](#4-writing-python-tasks)).

Although `HEASoftpy` is written in pure python, it does not rewrite 
the functions and tools already existing in `HEASoft`. A working
installation of `HEASoft` is therefore required.


## 2. Usage
After intallation (see [Installation](#3-installation)), `HEASoftpy` can
be used is several ways.

### 2.1 Calling the Tasks:
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
calcfov.py ra=... dec=...

```

### 2.2 Different Ways of Passing Parameters:
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
... # other parameters
fdump_task()

# or a combination of the above

```

Whenever a task in called, if any of the required parameters is missing, 
the user is prompted to enter a value.

Note that creatting a task object with `fdump_task = hsp.HSPTask('fdump')` does not actually call the task, it just initialize it. Only by doing `fdump_task(...)` that the task is called and paramters are queried if necessary.


### 2.3 Common `HEASoftpy` Parameters:
There are a few parameters that are common between all tasks:
- `verbose`: If `True`, print the task output to screen as the task runs. Default is `False`
- `noprompt`: Typically, HSPTask would check the input parameters and 
    queries any missing ones. Some tasks (e.g. pipelines) can run by using
    default values. Setting `noprompt=True`, disables checking and quering 
    the parameters. Default is `False`.
- `stderr`: If `True`, make `stderr` separate from `stdout`. The default
    is `False`, so `stderr` is written to `stdout`.


### 2.4 Finding Help for the Tasks:
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


## 3. Installation
Assuming you have `HEASoft` initialized and the environment variable `\$HEADAS` is defined, you can install `heasoftpy` in two ways:

#### - Install within the `HEASoft` tree:

1- Download the [latest version of heasoftpy](https://sed-gitlab.gsfc.nasa.gov/azoghbi/heasoftpy/-/archive/refactor/heasoftpy-refactor.tar.gz) to `$HEADAS/lib/python` (if `$HEADAS/lib/python` doesn't exist, please create it).

2- Rename or remove the `heasoftpy` folder if it exists.

3- Untar the downloaded file (creates a `heasoftpy` directory)
    
4- Rename the created `heasoftpy` folder to `heasoftpy_src`
    
5- From within `$HEADAS/lib/python`: make a soft link for `heasoftpy_src/heasofpy` : 
```sh
ln -s heasoftpy_src/heasofpy heasoftpy
```
    
6- Run the installer from the command line:
```sh
cd heasoftpy_src
python install.py
```
This process, which may take a few minutes, will install the python wrappers for the `HEASoft` tools, and any python-only tasks.

7- Lastly, make sure that `$HEADAS/lib/python` is included in your `PYTHONPATH` environment variable (so python can find the installed package), you may need to re-initialize `HEASoft` by sourcing the standard `HEASoft` setup script:
```sh
source $HEADAS/headas-init.sh  (Bourne shell variants)
#Or
source $HEADAS/headas-init.csh (C-shell variants)
```

#### - Install outside the `HEASoft` tree:

`heasoftpy` does not have to be inside the `HEASoft` tree as long as `HEASoft` is initialized (`$HEADAS` is defined), and `PYTHONPATH` is setup correctly. Assuming you want to install `heasoftpy` in some location `HEASOFTPY_LOC`, just repeat the above steps 1-6, replacing `$HEADAS/lib/python` with `HEASOFTPY_LOC`. Then, make sure `PYTHONPATH` includes your location `HEASOFTPY_LOC`. 


While the `install.py` script is running, check the screen or the `heasoftpy-install.log` for errors.

---
## 4. Writing Python Tasks
The core of `HEASoftpy` is the class `HSPTask`, which handles the parameter reading and setting (from to to the `.par` file).

It was written in a way that makes it easy for writing new codes that can be easily integrated within `HEASoft`. All that is needed, in addition to creating a `.par` file, is to create a subclass of `HSPTask` and implement a method `exec_task` that does the task function. An example is given in `packages/template`. The following is short snippet:

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
The `HSPTask` class provides a dictionary of input parameters in the variable `self.params`.

`HSPResult` is a simple container for the task output, which defines:
- `returncode`: a return code: 0 if the task executed without errors (int).
- `stdout`: standard output (str).
- `stderr`: standard error message (str).
- `params`: dict of user parameters in case the task changed them, used to update the .par file.
- `custom`: dict of any other variables returned by the task.

You can also define a method `task_docs` in `SampleTask` that returns a string of the documentations of the task. This will be appended to the docstring automatically generated from the `.par` parameter. For example:

```python

    def task_docs(self):
        docs = "*** Documentation for the sample code goes here! ***"
        return docs
```

## 5. Tutorials:
The [notebooks](notebooks) folder contains some jupyter notebook tutorials and usage examples.

- [Getting Started](notebooks/getting-started.ipynb): A quick walkthrough guide of the main features of the `HEASoftpy` package, and ways of calling and obtaining help for the tasks.

- [NuSTAR Data Analysis Example](notebooks/nustar_example.ipynb): This is a walkthough example of analyzing NuSTAR observation `60001110002` of the AGN in center of `SWIFT J2127.4+5654` using `HEASoftpy`. It includes examples of calling the calibration pipeline, and then extracting the source light curve.