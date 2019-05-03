"""

This package creates a Python interface into the High Energy
Astrophysics Science Archive (HEASARC) tools (commonly called FTools
or sometimes HTools, which will be used here). This initialization
file sets up functions and other attributes that can be accessed directly
at the module level.

"""

import collections
import csv
import importlib
import inspect
import logging
import os
import sys
import subprocess

logging.basicConfig(filename='heaspy_test.log', filemode='w',
                    level=logging.DEBUG)
LOGGER = logging.getLogger('inside heaspy')

THIS_MODULE = sys.modules[__name__]

class Heaspy():
    """
    Class to implement the Python interface to the HTools. It "replaces"
    the heaspy module, so that calls can be made via mechanisms like:
        import heaspy
        heaspy.ftlist(...)
    or
        from heaspy import *
        ftlist(...)
    """
    DEBUG = False
    DEBUG = True    # Uncomment for debugging, comment out for production

    PFILES_DIR = os.path.join(os.environ['HEADAS'], 'syspfiles')
    HEASPY_DIR = os.path.dirname(__file__)

    PARS_TO_IGNORE = ['asca.par', 'caltools.par', 'einstein.par', 'fimage.par',
                      'ftools.par', 'futils.par', 'gro.par', 'heasarc.par',
                      'rosat.par', 'time.par', 'vela5b.par', 'xte.par',
                      'cdemo.par', 'f77demo.par', 'perldemo.par', 'perldemo2.par',
                      'a2source.parin', 'abc.parin', 'ascaray.parin', 'bct.parin',
                      'bod2rmf.parin', 'bodgetvp.parin', 'detect.parin',
                      'earth2sun.parin', 'emapgen.parin', 'faintdfe.parin',
                      'fovdsp.parin', 'fxbary.parin', 'hkscale.parin',
                      'mkfilter2.parin', 'nh.parin', 'ofaintdfe.parin',
                      'roscc2utc.parin', 'sec2time.parin', 'sisrmg.parin',
                      'sqaplot.parin', 'time2sec.parin', 'timeconv.parin']

    def runtask(self, task_to_run, **kwargs):
        """ 
        Run the HTool program named in task_to_run, passing arguments named in
        kwargs. Returns a single string containing the combined output from stdout
        and stderr.
        """
        LOGGER.debug('entering runtask for %s', task_to_run)
        cmd_line_args = list()
        cmd_line_args.append(task_to_run)
        for kword in kwargs:
            cmd_line_args.append('{0}={1}'.format(kword, kwargs[kword]))
        task_proc = subprocess.Popen(cmd_line_args, stdout=subprocess.PIPE,
                                     stderr=subprocess.STDOUT)
        task_out, _ = task_proc.communicate()
        if isinstance(task_out, bytes):
            task_out = task_out.decode()
        return task_out

    def __getattr__(self, task_name, **kwargs):
        """
        Create a wrapper function which calls the HTools task program named in
        task_name, then add it to the 
        """
        LOGGER.debug('entering __getattr__ for %s', task_name)
        par_name = task_name + '.par'
        if not par_name in self.PARS_TO_IGNORE:
            par_path = os.path.join(self.PFILES_DIR, par_name)
            if os.path.exists(par_path):
                def wrapper(**kwargs):
                    task_output = self.runtask(task_name, **kwargs)
                    return task_output
                setattr(self, task_name, wrapper)
                return wrapper
            else:
                print('Could not find par file for {}'.format(task_name))
        else:
            print('Could not create {}'.format(task_name))

sys.modules[__name__] = Heaspy()
