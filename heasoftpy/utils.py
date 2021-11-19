import sys
import os
import subprocess
from .core import HSPTask, HSPTaskException


def _generate_fcn_docs(hspTask):
    """Generation function docstring for a heasoft task using fhelp
    
    Args:
        hspTask: HSPTask instance of the task of interest
    """
    
    if not isinstance(hspTask, HSPTask):
        raise TypeError('The wrong type given. HSPTask instance is needed')
        
    name = hspTask.name
    params = hspTask.all_params
    
    # parameter description #
    parsDesc = '\n'.join([
                    f'     {par:12} {"(Req)" if desc["required"] else "":6}: '
                    f'{desc["prompt"]} (default: {desc["default"]})'
        for par,desc in params.items()])
    # --------------------- #
    
    # get extra docs from the task #
    task_docs = hspTask.task_docs()
    
    # put it all together #
    docs = f"""
    Automatically generated function for Heasoft task {name}.
    Additional help may be provided below.
    
    Args:
{parsDesc}
\n\n
{task_docs}
    """
    return docs
    
    

def generate_fcn_code(task_name):
    """Create python function for task_name
    
    Args:
        task_name: name of the heasoft task
    
    """
    # instantiate the task wrapper
    hspTask = HSPTask(task_name)
    
    # generate docstring
    docs = _generate_fcn_docs(hspTask)
    
    # generate function text
    fcn = f"""
    
import sys
import os
import subprocess

if __name__ == '__main__':
    # this will be updated depending on where we want this installed
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
    from heasoftpy.core import HSPTask, HSPTaskException
    from heasoftpy.utils import process_cmdLine
else:    
    from ..core import HSPTask, HSPTaskException



def {task_name}(args=None, **kwargs):
    \"""
{docs}
    \"""

    {task_name}_task = HSPTask(name="{task_name}")
    {task_name}_task(args, **kwargs)


if __name__ == '__main__':
    {task_name}_task = HSPTask(name="{task_name}")
    cmd_args = process_cmdLine({task_name}_task)
    {task_name}_task(**cmd_args)

    """
    
    return fcn


def process_cmdLine(hspTask=None):
    """Process command line arguments into a dict
    
    hspTask is needed in case we want to print the help 
    text when -h is present
    
    """
    # we can make this complicated using argparse, but we start simple
    
    # The case of requesting help only; print and exit
    if len(sys.argv) == 2 and sys.argv[1] in ['-h', '--help']:
        print(_generate_fcn_docs(hspTask))
        sys.exit(0)
    
    args = {}
    for val in sys.argv[1:]:
        val_list = val.strip().split('=')
        if len(val_list) == 1:
            raise ValueError(f'Unable to parse parameter {val}. Please use: param=value')
        args[val_list[0]] = val_list[1]
        
    return args