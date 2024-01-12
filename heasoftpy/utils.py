import sys
import os
import subprocess
import glob
import tempfile
import logging
import contextlib
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
    Find a list of tasks from the HEADAS/syspfiles/pfiles_list.txt,
    or use the one stored with the code
    For every one, generate the python code in heasoftpy/module/

    pfiles_list.txt should have the format:
    heacore:fthelp.par
    attitude:aberattitude.par
    ...
    
    Args:
        tasks: a list of task names. If None, generate for all in 
            pfiles_list.txt
    
    Return:
        A string containing the list of generated files.
    """
    
    logger = logging.getLogger('heasoftpy-install')
    
    # here we are assuming HEADAS is defined. 
    # TODO: check this is the case when we are installing heasoftpy for the firs time
    if 'HEADAS' in os.environ:
        pfile_dir = os.path.join(os.environ['HEADAS'], 'syspfiles')
    else:
        msg = 'HEADAS not defined. Please initialize Heasoft!'
        logger.error(msg)
        raise HSPTaskException(msg)

    # list of tasks
    # get the list of module:task from pfiles_list.txt
    plist_file = f'{pfile_dir}/pfiles_list.txt'
    if not os.path.exists(plist_file):
        plist_file = f'pfiles_list.txt'
    if not os.path.exists(plist_file):
        msg = 'No pfiles_list.txt found'
        logger.error(msg)
        raise HSPTaskException(msg)
    logger.info(f'Using {plist_file}')

    # put the list of modules/tasks into a dict
    modules = {}
    for line in open(plist_file).readlines():
        module, task = line.split(':')
        task = task.split('.')[0]
        # if some specific tasks are requested, use them, otherwise use all
        if tasks is not None and task not in tasks:
            continue
        # if the par file does not exist, skip
        if not os.path.exists(f'{pfile_dir}/{task}.par'):
            logger.info(f'No par file found for task {task}');
            continue
        if not module in modules:
            modules[module] = []
        modules[module].append(task)

    #modules = {k:v for k,v in modules.items() if k in ['heacore', 'nustar']}

    ntasks = sum([len(v) for v in modules.values()])
    logger.info(f'Installing python wrappers. There are {ntasks} tasks!')

    # wrapper creation loop
    it = 0
    files_list = []
    for module, tasks in modules.items():
        logger.info(f'Installing {module} ...')
        outDir = os.path.join(os.path.dirname(__file__), module)
        init_txt = ''
        for task_name in tasks:
            it += 1
            logger.info(f'.. {it}/{ntasks} install {module}/{task_name} ... ')

            # skip python tool, skip
            pytask = os.path.join(os.environ['HEADAS'], 'bin', f'{task_name}.py')
            if os.path.exists(pytask):
                logger.info(f'.. skipping python tools ... ')
                continue

            hsp = HSPTask(task_name)
            fcn = hsp.generate_fcn_code()

            if not os.path.exists(outDir):
                os.mkdir(outDir)
            with open(f'{outDir}/{hsp.pytaskname}.py', 'w') as fp:
                fp.write(fcn)
            init_txt += f'from .{hsp.pytaskname} import {hsp.pytaskname}\n'
            files_list.append(f'heasoftpy/{module}/{hsp.pytaskname}.py')

            logger.info(f'.. done with {module}/{task_name}')

        if init_txt != '':
            with open(f'{outDir}/__init__.py', 'w') as fp:
                fp.write(init_txt)
            files_list.append(f'heasoftpy/{module}/__init__.py')
        logger.info(f'Done installing {module} ...')

    ## --- TEMPORARY UNTIL FCN DEPRECATION -- ##
    logger.info(f'Installing deprecated fcn.* ...')
    outDir = os.path.join(os.path.dirname(__file__), 'fcn')
    if not os.path.exists(outDir):
        os.mkdir(outDir)
    it = 0
    init_txt = ''
    for module, tasks in modules.items():
        if module in ['ftools', 'heacore', 'heagen', 'heasim', 'heasptools',
                      'heatools', 'attitude', 'Xspec']:
            continue
        logger.info(f'Installing {module} ...')
        for task_name in tasks:
            it += 1
            logger.info(f'.. {it}/{ntasks} install fcn/{task_name} ... ')

            # skip python tool, skip
            pytask = os.path.join(os.environ['HEADAS'], 'bin', f'{task_name}.py')
            if os.path.exists(pytask):
                logger.info(f'.. skipping python tools ... ')
                continue

            alternative = f'Use ``heasoftpy.{module}.{task_name}`` instead'
            depr_text = (
                '@deprecated(\n'
                'since="1.4",\n'
                f'message="heasoftpy.{task_name} is being '
                f'deprecated and will be removed. {alternative}",\n'
                f'alternative="{alternative}",\n'
                f'warning_type=HSPDeprecationWarning'
            ')')
            hsp = HSPTask(task_name)
            fcn = hsp.generate_fcn_code(deprecate_text=depr_text)
            init_txt += f'from .{hsp.pytaskname} import {hsp.pytaskname}\n'
            files_list.append(f'heasoftpy/fcn/{hsp.pytaskname}.py')

            with open(f'{outDir}/{hsp.pytaskname}.py', 'w') as fp:
                fp.write(fcn)
            logger.info(f'.. done with fcn/{task_name}')
        logger.info(f'Done installing {module} ...')
    if init_txt != '':
        with open(f'{outDir}/__init__.py', 'w') as fp:
            fp.write(init_txt)
    files_list.append(f'heasoftpy/fcn/__init__.py')
    logger.info(f'Done installing deprecated fcn.* ...')
    ## -------------------------------------- ##

    return files_list


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
        pDir = tempfile.NamedTemporaryFile().name + '.pfiles'
    elif os.path.exists(par_dir):
        if os.path.isdir(par_dir):
            create = False
        else:
            raise OSError(f'{par_dir} is not a directory. It cannot be used pfiles')
    else:
        pass
    
    if create:
        os.mkdir(pDir)
    
    # if we make here, things are good, so add pDir to PFILES
    # Note that we are not including ~/pfiles because it may cause issues 
    # for tasks that write parameters such as ftstat
    syspfile = os.path.join(os.environ['HEADAS'], 'syspfiles')
    os.environ['PFILES'] = f'{pDir};{syspfile}'
    return pDir


@contextlib.contextmanager
def local_pfiles_context(par_dir=None):
    """Create a conext environment with a temporary parameter file directory
    that can be run like:
    
    with local_pfiles_context(par_dir):
        # run tasks in parallel for exampel
        
    
    This is useful for scripting and running many tasks at the same time
    so that the tasks do not overwrite each other's pfiles.
    See https://heasarc.gsfc.nasa.gov/lheasoft/scripting.html.
    
    Parameters:
    -----------
        par_dir: str or None
            a user-specified directory. None means create a temporary one.
    """
    old_pfiles = os.environ['PFILES']
    pdir = local_pfiles(par_dir)
    try:
        yield
    finally:
        os.environ['PFILES'] = old_pfiles
        if os.path.exists(pdir):
            os.system(f'rm -rf {pdir}')
