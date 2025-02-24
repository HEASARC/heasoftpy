
Python interface to HEASoft
===========================

<a id="top"></a>

- [1. About](#about)
- [2. Usage](#usage)
    - [2.1 Calling the Tasks](#calling-the-tasks)
    - [2.2 Different Ways of Passing Parameters](#different-ways-of-passing-parameters)
    - [2.3 `HEASoftPy` Control Parameters](#heasoftpy-control-parameters)
    - [2.4 Finding Help for the Tasks](#finding-help-for-the-tasks)
- [3. Installation](#installation)
- [4. Re-creating function wrappers](#re-creating-function-wrappers)
- [5. Running Tasks in Parallel](#running-tasks-in-parallel)
- [6. User Guide and Tutorials](#tutorials)
- [7. Writing Python Tasks](#writing-python-tasks)


# 1. About

`HEASoftPy` is a Python 3 package that gives access to the `HEASoft`
tools using python. It provides python wrappers that call the
`HEASoft` tools, allowing for easy integration into other python
code.

`HEASoftPy` also provides a framework that allows for pure-python
tools to be developed and integrated within the `HEASoft` system 
(see [Writing Python Tasks](#4.-Writing-Python-Tasks)).
The IXPE tools are an example of mission tools developed in python.

Although `HEASoftPy` is written in pure python, it does not rewrite
the functions and tools already existing in `HEASoft`. A working
installation of `HEASoft` is therefore required.

[Back to Top](#top)

# 2. Usage

After installation (see [Installation](#3.-Installation)), `HEASoftPy` can
be used is several ways.

## 2.1 Calling the Tasks

1- Importing the task methods:
```python

import heasoftpy as hsp
hsp.ftlist(infile='input.fits', option='HC', outfile='STDOUT', ...)

```

2- Creating a `HSPTask` and invoking it:
```python

import heasoftpy as hsp
ftlist = hsp.HSPTask('ftlist')
ftlist(infile='input.fits', option='HC', outfile='STDOUT', ...)

```

3- For tasks written in python (e.g. `ixpecalcfov.py`), the tools can be used as usual from the command line, similar to the standard `HEASoft` tools:
```bash
ixpecalcfov[.py] ra=... dec=...
```
The `.py` extension is generally optional.

<hr style="border: 2px solid #fadbac" />

**For version 1.4 and above**
To avoid importing all tasks at once (more than 800), the tasks
have been grouped into separate modules.
Wrappers are still available in the heasoftpy.* namespace,
which import from the modules when the task is called.
So you can do lazy (delayed) import with:

```python
import heasoftpy as hsp
result = hsp.ftlist(infile='input.fits', option='T')
```
or full import with
```python
from heasoftpy.heatools import ftlist
result = ftlist(infile='input.fits', option='T')
```

To find the corresponding module name you can do:
```python
hsp.utils.find_module_name('ftlist')
heatools
```


### Task Names

Native `HEASoft` tasks have the same names in `HEASoftPy`. So a task like
`nicerclean` is called by `heasoftpy.nicerclean`, except for tasks
that have the dash symbol `-` in the name, which is replaced by an underscore `_`.
For example, the task `bat-burst-advocate` is available
with `heasoftpy.bat_burst_advocate`, etc.

[Back to Top](#top)

## 2.2 Different Ways of Passing Parameters
Passing parameters to a task can be done in several ways. For example:

```python

import heasoftpy as hsp
hsp.ftlist(infile='input.fits', option='HC', outfile='STDOUT', ...)

# or
params = {
    'infile': 'input.fits',
    'option': 'HC',
    'outfile': 'STDOUT',
    ...
}
hsp.ftlist(params)

# or
ftlist_task = hsp.HSPTask('ftlist')
ftlist_task(infile='input2.fits', option='HC', outfile='STDOUT', ...)
hsp.ftlist(ftlist_task)

# or
ftlist_task = hsp.HSPTask('ftlist')
ftlist_task.infile = 'input2.fits'
ftlist_task.option= 'HC'
ftlist_task.outfile = 'STDOUT'
... # other parameters
ftlist_task()

# or a combination of the above

```

Whenever a task in called, if any of the required parameters is missing, 
the user is prompted to enter a value. If the user knows that the passed
parameters are enough to run the task (e.g. pipeline tools), 
they can pass `noprompt=True`, to distable parameter prompt.

Note that creating a task object with `ftlist_task = hsp.HSPTask('ftlist')`
does not actually call the task, it just initializes it. 
Only by doing `ftlist_task(...)` is the task called and
parameters are queried if necessary.

[Back to Top](#top)

## 2.3 `HEASoftPy` Control Parameters
There are a few parameters that are common between all tasks:
- `verbose`: This can take several values. In all cases, the text printed by the
    task is captured, and returned in `HSPResult.stdout/stderr`. Additionally:
    - `0` (also `False` or `no`): Just return the text, no progress printing.
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

### 2.3.1 Special cases
If the `heasoftpy` task being called has an input parameter with a name `verbose`, `noprompt`
or `logfile`, then the above control parameters can be accessed by prepending them with `py_`,
so `verbose` becomes `py_verbose` etc. For example: the task `batsurvey_catmux` has a parameter
called `logfile`. If the you want to use both parameters, the call would be:
```python
heasoftpy.batsurvey_catmux(..., logfile='task.log', py_logfile='pytask.log')
```
with `'task.log'` logging the task activity, and `'pytask.log'` logging the python wrapper activity.

[Back to Top](#top)

## 2.4 Finding Help for the Tasks
The help for the tasks can be accessed in the standard python way, e.g. in ipython:
```python
hsp.ftlist?
# or
help(hsp.ftlist)
```

which will print something like the following, indicating the required parameters:
```
    Automatically generated function for Heasoft task ftlist.


    Parameters
    
    ----------

    infile       (Req) :  Input file name  (default: )
    option       (Req) :  Print options: H C K I T  (default: HC)
    outfile            :  Optional output file  (default: -)
    clobber            :  Overwrite existing output file?  (default: no)
    include            :  Include keywords list  (default: *)
    exclude            :  Exclude keywords list  (default: )
    section            :  Image section to print, eg, '2:8,1:10' (default: *)
    columns            :  Table columns to print  (default: *)
    rows               :  Table rows or ranges to print, eg, '2,6-8' (default: -)
    vector             :  Vector range to print, eg, '1-5'  (default: -)
    separator          :  Column separator string  (default:  )
    rownum             :  Print row number?  (default: yes)
    colheader          :  Print column header?  (default: yes)
    mode               :  Mode  (default: ql)


...
```
Scrolling down further, the help message will print the standard HEASoft help text from `fhelp`.
```
    --------------------------------------------------
       fhelp-generated text
    --------------------------------------------------
    NAME

       ftlist - List the contents of the input file.

    USAGE

       ftlist infile[ext][filters] option

    DESCRIPTION

       'ftlist' displays the contents of the input file. Depending on the
       value of the 'option' parameter, this task can be used to list any
       combination of the following:

         * a one line summary of the contents of each HDU (option = H)
         * the names, units, and ranges of each table column (option = C)
         * all or a selected subset of the header keywords (option = K)
         * the pixel values in a subset of an image (option = I)
         * the values in selected rows and columns of a table (option = T)

       If a specific HDU name or number is given as part of the input file
       name then only that HDU will be listed. If only the root name of the
       file is specified, then every HDU in the file will be listed.

```

[Back to Top](#top)

# 3. Installation
`heasoftpy` is installed automatically with `HEASoft` version 6.30 or newer.  Make sure you have python version >3.8, and the python dependencies installed (see step 1- below) before installing `HEASoft`. If you have an older version of `HEASoft`, the following steps can be used to install or update `heasoftpy` manually in an existing `HEASoft` installation.

Assuming you have `HEASoft` initialized and the environment variable `$HEADAS` is defined:

## - With Heasoft
`heasoftpy` is automatically installed with any new installation of `HEASoft` after version 6.30

## - Update to latest heasoftpy
Starting with `HEASoft 6.32`, you can update `heasoftpy` by running `hpyupdate`.  First, make sure that `HEASoft` is initialized and that the utilities `wget` and `tar` are available in your system `PATH`, then simply run
```sh
hpyupdate
```

## - Manual Install

1- Download the [latest version of heasoftpy](https://heasarc.gsfc.nasa.gov/FTP/software/lheasoft/release/heasoftpy-latest.tar)

2- Untar the file:
```sh
tar -xvf heasoftpy-latest.tar
cd heasoftpy
```

3- Install python dependencies:
```sh
pip install -r requirements.txt 
```

4- Generate the wrappers and install the package:
To install `heasoftpy` into the `$HEADAS` tree:
```
bash local-build.py
```
This will generate the python wrappers under `build/heasoftpy`. Errors will be printed in the `pip.log` file.

5- Move the `heasoftpy` folder from `build/heasoftpy` to `$HEADAS/lib/python`.
```sh
rm -r $HEADAS/lib/python/heasoftpy
mv build/heasoftpy $HEADAS/lib/python
```

6- Move the parameter files, executables and help files (if any) to their location in the `$HEADAS` tree:
```sh
mv build/bin/* $HEADAS/bin
mv build/syspfiles/* $HEADAS/syspfiles
mv build/help/* $HEADAS/help
```


## - Install Outside the `HEASoft` tree

`heasoftpy` does not have to be inside the `HEASoft` tree as long as `HEASoft` is initialized. Inside the newly download `heasoftpy` folder, do: `pip install .`



[Back to Top](#top)

# 4. Re-creating function wrappers

There may be times when a `heasoftpy` function needs 
to be created for an installed `HEASoft` task 
(for example, if a new `HEASoft` component is added to 
`HEASoft` after `heasoftpy` was initially installed). 
`heasoftpy` wrappers can be created (or re-created) using 
the `heasoftpy.utils.generate_py_code`function.  For example
to generate a heasoftpy function wrapper for the NICERDAS
tool `nibackgen3c50`, do the following in python:

```python
from heasoftpy.utils import generate_py_code
tasks = ['nibackgen3c50']
generate_py_code(tasks=task)
```
You can also start a fresh `heasoftpy` installation as detailed in the [Installation](3.-Installation) section.


---

[Back to Top](#top)

# 5. Running Tasks in Parallel
As discussed in the [PARALLEL BATCH PROCESSING](https://heasarc.gsfc.nasa.gov/lheasoft/scripting.html), most `heasoft` (and hence `heasoftpy`) tasks use parameter files whose location is managed by the `PFILES` environment variable. Parallel calls to the same task will likely end up using the same parameter file and may cause unintended parameter changes. Users may use the suggestions in the link above, however when using python scripting, it may be convenient to use the context manager method `heasoftpy.utils.local_pfiles_context`. Including all parallel tasks inside a `with` statement, will ensure that temporary parameter files are used. The following gives an example:

```python
from multiprocessing import Pool
import heasoftpy as hsp
from heasoftpy import nicer


def worker(args):
    """Run individual tasks"""
    with hsp.utils.local_pfiles_context():
        # call the tasks of interest
        out = nicer.nicerl2(...)
        # other tasks
        # ...
    
    return output

nproc = 5
with Pool(nproc) as p:
    result = p.map(worker, [1, 2, 3, 4, 5])
        
```

---

[Back to Top](#top)

# 6. Tutorials
The following notebooks contain some tutorials and usage examples.

- [Getting Started](getting-started.html): A quick walkthrough guide of the main features of the `HEASoftPy` package, and ways of calling and obtaining help for the tasks.

- [NuSTAR Data Analysis Example](nustar-example.html): This is a walkthrough example of analyzing NuSTAR observation `60001110002` of the AGN in center of `SWIFT J2127.4+5654` using `HEASoftPy`. It includes examples of calling the calibration pipeline, and then extracting the source light curve.

- [NICER Data Analysis Example](nicer-example.html): This is a walkthrough example of analyzing NICER data using `HEASoftPy` and `PyXspec`.


[Back to Top](#top)

# 7. Writing Python Tasks
The core of `HEASoftPy` is the class `HSPTask`, which handles the parameter reading and setting (from the `.par` file).

It was written in a way that makes it easy for writing new codes that can be easily integrated within `HEASoft`. All that is needed, in addition to creating a `.par` file, is to create a subclass of `HSPTask` and implement a method `exec_task` that does the task function. An example is given in `template`. The following is short snippet:

```python

import heasoftpy as hsp

class SampleTask(hsp.HSPTask):
    """New Task"""
    
    name = 'sampletask'
    
    def exec_task(self):
        
        # model parameters as a dict
        usr_params = self.params
        
        # write your task code here #
        # ...
        # ...
        # ------------------------- #
        
        # finally return a HSPResult
        return hsp.HSPResult(0, out, None, usr_params)
        
```