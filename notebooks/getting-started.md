
## Introduction
`heasoftpy` is a python wrapper around the `HEASoft` tools.

This is a quick "Getting Started" guide. It contains a walkthrough the main features of the package

The first thing we need is to import the `heasoftpy` package. 
Please follow the installation instructions in in `README` file.


```python
import sys
import os
import heasoftpy as hsp
```

```python
# check heasoftpy version
print(hsp.__version__)
```

A general package help can printed by doing `hsp?` or `hsp.help()`

```python
hsp.help()
```

## Example 1: Exploring The Content of a Fits File with `ftlist`

The simplest way to run a task is call the function directly (after installing the package) as: `hsp.task_name(...)`

Here too, we can print the help text for a task using standard python help: `task_name?`


```python
from heasoftpy.heatools import ftlist
ftlist?
```

To see the module that contains ftlist, use (available in heasoftpy >1.5),
```python
heasoftpy.utils.hsp.utils.find_module_name('ftlist')
# it gives: heatools
```
So the import is `from heasoftpy.heatools import ftlist`.

`heasoftpy.ftlist` should work too. It does the import when it is called.

For `ftlist`, there two required inputs: `infile` and `option`, so that both
parameters need to be provided, otherwise, we will get prompted for the missing parameters

```python
result = hsp.ftlist(infile='../tests/test.fits', option='T')
```

Running a task returns an `HSPResult` instance, which is a simple container for the results that contains:
- `returncode`: a return code: 0 if the task executed without errors (int).
- `stdout`: standard output (str).
- `stderr`: standard error message (str).
- `params`: dict of user parameters in case the task changed them, used to update the .par file.
- `custom`: dict of any other variables to returned by the task.

In this case, we may want to just print the output as:

```python
print('return code:', result.returncode)
print(result.stdout)
```

A `returncode = 0` indicates the task executed without problems.

We can print the content `result` to see all the returns of the task:

```python
print(result)
```

We can modify the parameters returned in results, and pass them again to the task.

Say we want to print the column header:

```python
params  = result.params
params['colheader'] = 'yes'
result2 = hsp.ftlist(params)

print(result2.stdout)
```

Notice how the column header is printed now!

If we forget to pass a required parameter, we will be prompted for it. For example:

```python
result = hsp.ftlist(infile='../tests/test.fits')
```

In this case, parameter `ftlist:option` was missing, so we are prompted for it, and the default value is printed between brackets: `(T)`, we can type a value, just press Return to accept the default value.

---

For tasks that take longer to run, the user may be interested in the seeing the output as the task runs. There is a `verbose` option to print the output of the command similar to the standard output in command line tasks.

```python
result = hsp.ftlist(infile='../tests/test.fits', option='T', verbose=True)
```

---

There is an alternative way to calling a task, and that is by creating an instance of `HSPTask` and calling it. For the example of `ftlist`, we would do:

```python
# create a task object
ftlist = hsp.HSPTask('ftlist')
```

the `ftlist` instance acts just like the function `hsp.ftlist` above.

```python
# run the task
out = ftlist(infile='../tests/test.fits', option='T')
print(out.stdout)
```

The parameters of the task are attributes of the `HSPTask` object (called `ftlist` here), so they can be easily modified:

```python
ftlist.colheader = 'no'
out = ftlist()
print(out.stdout)
```

Note that the line `out = ftlist()` executes without querying for parameters because it uses parameters from the previous run, which are stored in `ftlist.params` and returned in `out.params`


---

### Disable parameter query

For some tasks, particularly pipelines, the user may want to runs the task without querying all the parameters. 
In that case, we can pass the `noprompt=True` when calling the task, and `heasoftpy` will run the task without
checking the parameters. For example, to process the NuSTAR observation `60001111003`, we can do:

```python
from heasoftpy import nustar
r = nustar.nupipeline(indir='60001111003', outdir='60001111003_p', steminputs='nu60001111003', 
                   noprompt=True, verbose=True)
```

this will call `nupipeline` without querying all parameters (using the defaults), and printing all progress as it runs (`verbose=True`)
<!-- #endregion -->

