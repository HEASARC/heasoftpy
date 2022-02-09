
import sys
import os
import logging
import glob
import importlib
import shutil
import subprocess

# add heasoftpy location to sys.path as it is not installed yet
current_dir = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, current_dir)

# Where to install the pure-python executable and parameter file #
if not 'HEADAS' in os.environ:
    raise RuntimeError('heasoft needs to be initialized before running this script')
#exe_install_dir = os.path.join(os.environ['HEADAS'], 'bin')
#par_install_dir = os.path.join(os.environ['HEADAS'], 'syspfiles')
#help_install_dir = os.path.join(os.environ['HEADAS'], 'help')
exe_install_dir = os.path.join('build', 'bin')
par_install_dir = os.path.join('build', 'syspfiles')
help_install_dir = os.path.join('build', 'help')
package_dir = os.path.join(current_dir, 'heasoftpy', 'packages')



## --- setup logger --- ##
logger = logging.getLogger('heasoftpy-install')
logger.setLevel(logging.DEBUG)

# log to a file 
fh = logging.FileHandler('heasoftpy-install.log', mode='w')
fh.setLevel(logging.DEBUG)

# log to screen
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# create formatter and add it to the handlers
tformat = '%Y-%m-%d %H:%M:%S'
formatter = logging.Formatter(
    '%(asctime)s - %(levelname)5s - %(filename)s - %(message)s', tformat)
fh.setFormatter(formatter)
formatter = logging.Formatter('%(asctime)s - %(levelname)5s - %(message)s', tformat)
ch.setFormatter(formatter)

# add the handlers to the logger
logger.addHandler(fh)
logger.addHandler(ch)
## -------------------- ##



## ---------------------------------- ##
## python wrappers for built-in tools ##
def _create_py_wrappers():
    
    # the following prevents sub-package in heasoftpy.packages from being imported
    # as they may depend on the functions in heasoftpy.fcn, that we will install here
    os.environ['__INSTALLING_HSP'] = 'yes'
    from heasoftpy.utils import generate_py_code
    
    
    logger.info('-'*30)
    logger.info('Creating python wrappers ...')
    try:
        generate_py_code()
    except:
        logger.error('Failed in generating python wrappers')
        raise
    logger.info('Python wrappers created sucessfully!')
    logger.info('-'*30)
    
    # remove the __INSTALLING_HSP variable we added at the start
    del os.environ['__INSTALLING_HSP']
## ---------------------------------- ##



## ---------------------------- ##
## installing pure-python tools ##


# get a list of package names
package_dir = os.path.join(current_dir, 'heasoftpy', 'packages')
packages = glob.glob(f'{package_dir}/*')
packages = [os.path.basename(p) for p in packages if not '__' in p]
# remove template from the list of packages.
if 'template' in packages:
    packages.remove('template')
    
# exclude python packages that are not requested by the user.
# Find the list from the list of folders in the component-level directory
component_level = glob.glob('../..')
# first make sure we are in a standard location: heacore/heasoftpy/install.py
# if not, do nothing
if 'heacore' in component_level:
    for package in packages:
        if not package in component_level:
            # remove package from the list of packages to be installed
            packages.remove(package)
            
            # remove the folder completely
            os.rmdir(os.path.join(package_dir, package))
    

    # exclude python packages that are not requested by the user.
    # Find the list from the list of folders in the component-level directory
    component_level = glob.glob('../..')
    # first make sure we are in a standard location: heacore/heasoftpy/install.py
    # if not, do nothing
    if 'heacore' in component_level:
        for package in packages:
            if not package in component_level:
                # remove package from the list of packages to be installed
                packages.remove(package)

logger.info(f'Found {len(packages)} in heasoftpy/packages')

exe_list, par_list = [], []
for package in packages:
    logger.info(f'     installing package: {package} ...')
    # do we have a setup.py file?
    setupfile = os.path.join('heasoftpy', 'packages', package, 'setup.py')
    if not os.path.exists(setupfile):
        logger.error(f'Package {package} has no setup.py file. Stopping.')
        sys.exit(1)
    else:
        logger.info(f'     setup file found ...')
        # try reading the setup.py file
        try:
            with open(setupfile) as fp:
                exec(fp.read())
        except:
            logger.error(f'Cannot process setup.py in {package}. Stopping.')
            raise
    
    # try importing the package
    try:
        tmpmod = importlib.import_module(f'heasoftpy.packages.{package}')
    except:
        logger.error(f'Attempting to import "{package}" failed. See error message below.')
        raise
    logger.info(f'     package "{package}" sucessfully imported.')

    
    # loop through the task, and install them one by one.
    for task in tasks:
        
        # if task is str, we look for task files in the package
        # or a directory that has the name of the task
        if isinstance(task, str):
            logger.info(f'     installing task: {task}')
            # look for exec and par file:
            taskdir = os.path.join(package_dir, package, task)
            if os.path.isdir(taskdir):
                logger.info(f'     found task package: {taskdir}')
                exe_file = os.path.join(taskdir, f'{task}.py')
                par_file = os.path.join(taskdir, f'{task}.par')
            else:
                logger.info(f'     searching for task module: {task}')
                exe_file = os.path.join(package_dir, package, f'{task}.py')
                par_file = os.path.join(package_dir, package, f'{task}.par')
        
        # we have an explicit dict that points to location of executable and par files
        elif isinstance(task, dict):
            logger.info(f'     installing: {list(task.keys())[0]}')
            exe_file, par_file = [os.path.join(package_dir, package, p) 
                                      for p in list(task.values())[0]]
        
        # we don't know how to install the task
        else:
            msg = f'Failed processing the setup file for task: {task}'
            logger.error(msg)
            raise ValueError(msg)
        
        # checking all files exist
        if not os.path.exists(exe_file):
            msg = f'Could not find executable {exe_file}'
            logger.error(msg)
            raise FileNotFoundError(msg)
        if not os.path.exists(par_file):
            msg = f'Could not find parameter file {par_file}'
            logger.error(msg)
            raise FileNotFoundError(msg)
        
        # copy files to their right location #
        logger.info('     copying task files')
        exe_dest = os.path.join(exe_install_dir, os.path.basename(exe_file))
        par_dest = os.path.join(par_install_dir, os.path.basename(par_file))
        
        # copy files make the exe file executable
        # uncomment the following once it is real install
        shutil.copyfile(exe_file, exe_dest)
        shutil.copyfile(par_file, par_dest)
        subprocess.call(['chmod', '755', exe_dest])
if len(packages) > 0:
    logger.info('Pure-python tools installed sucessfully')
del os.environ['__INSTALLING_HSP']
## ---------------------------- ##