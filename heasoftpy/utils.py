import sys
import os
import subprocess
from .core import HSPTask, HSPTaskException


MODULE = sys.modules[__name__]


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
    
    # call fhelp #
    cmd  = os.path.join(os.environ['HEADAS'], 'bin/fhelp')
    try:
        proc = subprocess.Popen([cmd, f'task={name}'], stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        proc_out, proc_err = proc.communicate()
    except:
        print(f'Failed in running fhelp to obtain docs for {name}')
    # ---------- #
    
    # convert fhelp output from byte to str #
    try:
        if not proc_err:
            fhelp = proc_out.decode()
        else:
            fhelp = proc_err.decode()
    except:
        # we can be more specific in trapping
        print(f'Failed in processing fhelp return for {name}')
    fhelp.replace('"""', '')
    # ------------------------------------- #
    
    # put it all together #
    docs = f"""
    Automatically generated function for Heasoft task {name}.
    For detailed help, scroll down to the fhelp text.
    
    Args:
{parsDesc}
\n{'#'*70}
{'-'*50}\n   The following has been generated from fhelp\n{'-'*50}\n
{fhelp}
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
else:    
    from ..core import HSPTask, HSPTaskException



def {task_name}(*args, **kwargs):
    \"""
{docs}
    \"""

    {task_name} = HSPTask(name="{task_name}")
    {task_name}()


if __name__ == '__main__':
    {task_name}()

    """
    
    with open(f'{task_name}.py', 'w') as fp:
        fp.write(fcn)