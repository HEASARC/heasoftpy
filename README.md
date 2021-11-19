Python interface to HeaSoft
===========================

## Content
- [About](#About)
- [Usage](#Usage)
- [Installation](#Installation)


## About:
`HEASoftpy` is a Python 3 package that gives access to the `HEASoft` 
tools using python. It provies python wrappers that calls the 
`HEASoft` tools, allowing for easy integration into other python
code.

`HEASoftpy` also provides the framework that allows for pure-python
tools to be integrated within the `HEASoft` system.

Although `HEASoftpy` is written in pure python, it does NOT rewrite 
the functions and tools already existing in `HEASoft`. A working
installation of `HEASoft` is therefore required.


## Usage
After intallation (see [installation](#Installation)), `HEASoftpy` can
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


```

Whenver a task in called, if any of the required parameters is missing, 
the user is prompted to enter a value.


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
