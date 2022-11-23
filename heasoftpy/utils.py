import sys
import os
import subprocess
import glob
import logging
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
    
    # make verbose=1 default
    if not 'verbose' in args.keys():
        args['verbose'] = 1
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
    
    logger = logging.getLogger('heasoftpy-install')
    
    # here we are assuming HEADAS is defined. 
    # TODO: check this is the case when we are installying heasoftpy for the firs time
    if 'HEADAS' in os.environ:
        pfile_dir = os.path.join(os.environ['HEADAS'], 'syspfiles')
    else:
        msg = 'HEADAS not defined. Please initialize Heasoft!'
        logger.error(msg)
        raise HSPTaskException(msg)
        
    
    # list of tasks
    if tasks is None:
        par_files = glob.glob(f'{pfile_dir}/*.par')
        tasks     = [os.path.basename(file[:-4]) for file in par_files]
    else:
        if not isinstance(tasks, (list, )) and not isinstance(tasks[0], str):
            msg = 'tasks has to be a list of task names'
            logger.error(msg)
            raise HSPTaskException(msg)
    
    
    ntasks = len(tasks)
    logger.info(f'Installying python wrappers. There are {ntasks} tasks!')
    
    # loop through the tasks and generate and save the code #
    outDir = os.path.join(os.path.dirname(__file__), 'fcn')
    
    for it,task_name in enumerate(tasks):
        logger.info(f'.. {it+1}/{ntasks} install {task_name} ... ')
        
        # if it is already a python tool, skip
        pytask = os.path.join(os.environ['HEADAS'], 'bin', f'{task_name}.py')
        if os.path.exists(pytask):
            logger.info(f'.. skipping python tools ... ')
            continue
        
        hsp = HSPTask(task_name)
        fcn = hsp.generate_fcn_code()
        with open(f'{outDir}/{hsp.pytaskname}.py', 'w') as fp: 
            fp.write(fcn)
        logger.info('done!')
    

def local_pfiles(par_dir=None):
    """Create a local parameter folder and add it to $PFILES
    
    This is useful for scripting and running many tasks at the same time
    so that the tasks do not overwrite each other's pfiles.
    See https://heasarc.gsfc.nasa.gov/lheasoft/scripting.html.
    
    Args:
        par_dir: a user-specified directory. None means create a temporary
            one.
    
    """
    
    # we need heasoft initialized
    if not 'HEADAS' in os.environ:
        raise HSPTaskExeception('HEADAS not defined. Please initialize heasoft')
    
    # do we have PFILES defined for the system pfiles?
    if not 'PFILES' in os.environ:
        os.environ['PFILES'] = os.path.join(os.environ['HEADAS'], 'syspfiles')
        
    # did the user provide a directory?
    create = True
    pDir   = par_dir
    if par_dir is None:
        pDir = os.path.join('/tmp', str(os.getpid()) + '.pfiles.tmp')
    elif os.path.exists(par_dir):
        if os.path.isdir(par_dir):
            create = False
        else:
            raise OSError(f'{par_dir} is not a directory. It cannot be used pfiles')
    else:
        pass
    
    if create:
        try:
            os.mkdir(pDir)
        except:
            raise OSError(f'Cannot create parameter directory {pDir}')
    
    # if we make here, things are good, so add pDir to PFILES
    # Note that we are not including ~/pfiles because it may cause issues 
    # for tasks that write parameters such as ftstat
    syspfile = os.path.join(os.environ['HEADAS'], 'syspfiles')
    os.environ['PFILES'] = f'{pDir};{syspfile}'
    return pDir