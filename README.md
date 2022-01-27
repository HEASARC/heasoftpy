Python interface to HeaSoft
===========================

## Content
- [1. About](#1.-About)
- [2. Usage](#2.-Usage)
    - [2.1 Calling the Tasks](#2.1-Calling-the-Tasks)
    - [2.2 Different Ways of Passing Parameters](#2.2-Different-Ways-of-Passing-Parameters)
    - [2.3 `HEASoftpy` Control Parameters](#2.3-HEAsoftpy-Control-Parameters)
    - [2.4 Finding Help for the Tasks](#2.4-Finding-Help-for-the-Tasks)
- [3. Installation](#3.-Installation)
- [4. Writing Python Tasks](#4.-Writing-Python-Tasks)
- [5. User Guide and Tutorials](#5.-Tutorials)


## 1. About
`HEASoftpy` is a Python 3 package that gives access to the `HEASoft` 
tools using python. It provies python wrappers that call the 
`HEASoft` tools, allowing for easy integration into other python
code.

`HEASoftpy` also provides a framework that allows for pure-python
tools to be developed and integrated within the `HEASoft` system (see [Writing Python Tasks](#4.-Writing-Python-Tasks)).

Although `HEASoftpy` is written in pure python, it does not rewrite 
the functions and tools already existing in `HEASoft`. A working
installation of `HEASoft` is therefore required.


## 2. Usage
After intallation (see [Installation](#3.-Installation)), `HEASoftpy` can
be used is several ways.

### 2.1 Calling the Tasks
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

3- For tasks written in python (e.g. `ixpecalcfov.py`), the tools can be used as usual from the command line, similar to the standard `HEASoft` tools:
```bash
ixpecalcfov.py ra=... dec=...

```

#### Task Names:
Native `heasoft` tasks have the same names in `heasfotpy`. So a task like `nicerclean` 
is called by `heasoftpy.nicerclean`, except for tasks that have the dash symbol `-` in the name,
which is replaced by an underscore `_`. So for example, the task `ut-swifttime` is available
with `heasoftpy.ut_swifttime`, etc.


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


### 2.3 `HEASoftpy` Control Parameters
There are a few parameters that are common between all tasks:
- `verbose`: This can take several values. In all cases, the text printed by the
    task is captured, and returned in `HSPResult.stdout/stderr`. Addionally:
    - `0` (also `False` or `no`): Just return the text, no progress prining.
    - `1` (also `True` or `yes`): In addition to capturing and returning the text,
        task text will printed into the screen as the task runs.
    - `2`: Similar to `1`, but also prints the text to a log file.
    - `20`: In addition to capturing and returning the text, log it to a file, 
        but not to the screen. 
        In both cases of `2` and `20`, the default log file name is {taskname}.log. 
        A `logfile` parameter can be passed to the task to override the file name.
- `noprompt`: Typically, HSPTask would check the input parameters and 
    queries any missing ones. Some tasks (e.g. pipelines) can run by using
    default values. Setting `noprompt=True`, disables checking and querying 
    the parameters. Default is `False`.
- `stderr`: If `True`, make `stderr` separate from `stdout`. The default
    is `False`, so `stderr` is written to `stdout`.

#### 2.3.1 Special cases
If the `heasoftpy` task being called has an input parameter with a name `verbose`, `noprompt`
or `logfile`, then the above control parameters can be accessed by prepending them with `py_`,
so `verbose` becomes `py_verbose` etc. For example: the task `batsurvey_catmux` has a parameter
called `logfile`. If the you want to use both parameters, the call would be:
```python
heasoftpy.batsurvey_catmux(..., logfile='task.log', py_logfile='pytask.log')
```
with `'task.log'` logging the task activity, and `'pytask.log'` logging the python wrapper activity.


### 2.4 Finding Help for the Tasks
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
`heasoftpy` is generally installed automatically installed when installing `HEAsoft`, make sure you have python version >3.7, and the python dependencies installed (see step 1- below) before installing `HEAsoft`. The following steps can be used to install or update `heasoftpy` manually after `HEAsoft` is installed.

Assuming you have `HEASoft` initialized and the environment variable `$HEADAS` is defined:

#### - Install within the `HEASoft` tree

1- Ensure you have `python>=3.7` installed. Install the latest versions of the python dependencies:
```sh
pip install numpy scipy astropy pytest
# or, if using conda:
conda install numpy scipy astropy pytest
```

2- Download the [latest version of heasoftpy](https://heasarc.gsfc.nasa.gov/FTP/software/lheasoft/release/heasoftpy.tar)
```sh
wget https://heasarc.gsfc.nasa.gov/FTP/software/lheasoft/release/heasoftpy.tar
```
or 
```sh
curl -O https://heasarc.gsfc.nasa.gov/FTP/software/lheasoft/release/heasoftpy.tar
```

3- Untar the file:
```sh
tar -xvf heasoftpy.tar
cd heasoftpy
```

4- Collect the pacakges:
```
python setup.py build
```
This will generate the python wrappers under `build/lib/heasoftpy`. Check the `heasoftpy-install.log` for errors.

5- Move the created `heasoftpy` folder to `$HEADAS/lib/python` (if `$HEADAS/lib/python` doesn't exist, please create it).
```sh
mv build/lib/heasoftpy $HEADAS/lib/python
```

6- Move the parameter files, executables and help files (if any) to their location in the `$HEADAS` tree:
```sh
mv build/bin/* $HEADAS/bin
mv build/syspfiles/* $HEADAS/syspfiles
mv build/help/* $HEADAS/help
```

#### - Install outside the `HEASoft` tree

`heasoftpy` does not have to be inside the `HEASoft` tree as long as `HEASoft` is initialized (`$HEADAS` is defined), and `PYTHONPATH` is setup correctly. Assuming you want to install `heasoftpy` in some location `HEASOFTPY_LOC`, just repeat the above steps 1-5, replacing `$HEADAS/lib/python` with `HEASOFTPY_LOC`. Then, make sure `PYTHONPATH` includes your location `HEASOFTPY_LOC`. 


---
## 4. Writing Python Tasks
The core of `HEASoftpy` is the class `HSPTask`, which handles the parameter reading and setting (from the `.par` file).

It was written in a way that makes it easy for writing new codes that can be easily integrated within `HEASoft`. All that is needed, in addition to creating a `.par` file, is to create a subclass of `HSPTask` and implement a method `exec_task` that does the task function. An example is given in `packages/template`. More details can be found in `heasoftpy/packages/template/__init__.py`. The following is short snippet:

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


## 5. Tutorials
The following notebooks contain some tutorials and usage examples.

- [Getting Started](getting-started.html): A quick walkthrough guide of the main features of the `HEASoftpy` package, and ways of calling and obtaining help for the tasks.

- [NuSTAR Data Analysis Example](nustar_example.html): This is a walkthough example of analyzing NuSTAR observation `60001110002` of the AGN in center of `SWIFT J2127.4+5654` using `HEASoftpy`. It includes examples of calling the calibration pipeline, and then extracting the source light curve.

- [NICER Data Analysis Example](nicer-processing.html): This is a walkthough example of analyzing NICER data using `HEASoftpy` and `pyXspec`.