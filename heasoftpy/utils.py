import sys
import os
import subprocess
import glob
from .core import HSPTask, HSPTaskException
    


def process_cmdLine(hspTask=None):
    """Process command line arguments into a dict
    
    hspTask is needed in case we want to print the help 
    text when -h is present
    
    """
    # we can make this complicated using argparse, but we start simple
    
    # The case of requesting help only; print and exit
    if len(sys.argv) == 2 and sys.argv[1] in ['-h', '--help']:
        print(hspTask._generate_fcn_docs())
        sys.exit(0)
    
    args = {}
    for val in sys.argv[1:]:
        val_list = val.strip().split('=')
        if len(val_list) == 1:
            raise ValueError(f'Unable to parse parameter {val}. Please use: param=value')
        args[val_list[0]] = val_list[1]
        
    return args


def generate_py_code(tasks=None):
    """Generate python code for the built-in heasoft tools
    
    This is meant to run once when installing the software.
    Find a list of tasks from the .par files in HEADAS/syspfiles.
    For every one, generate the python code in heasoftpy/fcn/
    
    
    Args:
        tasks: a list of task names. If None, generate for all in 
            $HEASDAS/syspfiles/*par
    
    Return:
        None
    """
    
    # here we are assuming HEADAS is defined. 
    # TODO: check this is the case when we are installying heasoftpy for the firs time
    if 'HEADAS' in os.environ:
        pfile_dir = os.path.join(os.environ['HEADAS'], 'syspfiles')
    else:
        raise HSPTaskException('HEADAS not defined. Please initialize Heasoft!')
        
    
    # list of tasks
    if tasks is None:
        par_files = glob.glob(f'{pfile_dir}/*.par')
        tasks     = [os.path.basename(file[:-4]) for file in par_files]
    else:
        if not isinstance(tasks, (list, )) and not isinstance(tasks[0], str):
            raise HSPTaskException('tasks has to be a list of task names')
    
    
    ntasks = len(tasks)
    print(f'Installying python wrappers. There are {ntasks} tasks!')
    
    # loop through the tasks and generate and save the code #
    outDir = os.path.join(os.path.dirname(__file__), 'fcn')
    
    for it,task_name in enumerate(tasks):
        print(f'.. {it+1}/{ntasks} install {task_name} ... ', end='')
        hsp = HSPTask(task_name)
        fcn = hsp.generate_fcn_code()
        with open(f'{outDir}/{hsp.pyname}.py', 'w') as fp: 
            fp.write(fcn)
        print('done!')
    
    