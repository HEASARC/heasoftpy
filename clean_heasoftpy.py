#!/usr/bin/env python

"""
Removes Python files that correspond to the HEASOFT parameter files and which
were (most likely) created by the heasoftpy.__init__.
"""

import argparse
import datetime
import logging
import os
import shutil
import sys

KEEP_FILES = []

NOW_STR = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
CUR_DIR = os.path.dirname(os.path.realpath(__file__))

HEADAS_DIR = os.environ['HEADAS']
HEASOFTPY_DIR = CUR_DIR # os.path.join(CUR_DIR, 'heasoftpy')

DEFAULT_DEFS_DIR = os.path.join(HEASOFTPY_DIR, 'defs')
#HEASOFTPY_DIR = os.path.join(CUR_DIR, 'write_fns') # from comparison vs "onthefly"

HOLDING_DIR = '/tmp/heasoftpy_holding_{}'.format(NOW_STR)
PY_VER = str(sys.version_info[0]) + str(sys.version_info[1])

# The following function duplcates code in __init__.py, but the
# goal is to avoid dependencies on the heasoftpy code.
def _find_pfiles_dir():
    """
    "Private" function to extract the system pfiles directory from the PFILES
    environment variable
    """

    def get_dir_from_parts(parts):
        """
        Internal helper function for searching a list of directories for the
        sys pfiles directory
        """
        the_dir = None
        for pf_part in parts:
            if (pf_part.find('heasoft') != -1) and (pf_part.find('syspfiles') != -1):
                the_dir = pf_part
                break
        return the_dir

    pfiles_dir = None
    pfiles_var = os.environ['PFILES']
    pfiles_parts = pfiles_var.split(';')
    if len(pfiles_parts) == 1:
        pfiles_parts = pfiles_var.split(':')
        if len(pfiles_parts) == 1:
            pfiles_dir = pfiles_var
        else:
            pfiles_dir = get_dir_from_parts(pfiles_parts)
    else:
        pfiles_dir = get_dir_from_parts(pfiles_parts)
    return pfiles_dir
PFILES_DIR = _find_pfiles_dir()

#2345678901234567890123456789012345678901234567890123456789012345678901234567890

def clean_file(task_file, task_file_path, logger):
    """
    Moves the file specified in task_file_path to HOLDING_DIR (does this by
    copying the file then removing the original).
    """
    dest_path = os.path.join(HOLDING_DIR, task_file)
    logger.info('Copying %s to holding area in /tmp', task_file_path)
    shutil.copyfile(task_file_path, dest_path)
    logger.info('Removing %s.', task_file_path)
    os.remove(task_file_path)

def clean_pyc_file(task_name, pycache_dir, defs_dir):
    """
    Deletes the .pyc file corresponding to task_name ... or at least tries to
    """
    deleted = False

    pycache_file_path = os.path.join(pycache_dir, task_name + '.pyc')

    if os.path.exists(pycache_file_path):
        os.remove(pycache_file_path)
        deleted = True
    else:
        pycache_file_path = os.path.join(defs_dir, '__pycache__',
                                         task_name.replace('-', '_') +
                                         '.cpython-' + PY_VER + '.pyc')
        if os.path.exists(pycache_file_path):
            os.remove(pycache_file_path)
            deleted = True
    return deleted, pycache_file_path

def delete_files(defs_dir, pfiles_list, logger):
    """ Loop through the par files, deleting the corresponding Python file """
    pycache_dir = find_pycache_dir(defs_dir)
    file_count = 0
    pyc_file_count = 0
    for pfile in pfiles_list:
        # rstrip() didn't work below; it removed stuff that should have stayed
        task_name = os.path.basename(pfile).rsplit('.')[0].replace('-', '_')
        task_file = '.'.join([task_name, 'py'])

        # Since Python doesn't allow a dash ('-') in a function name, the
        # file/function names will have an underscore ('_') where the par file
        # has a dash.
        task_file_path = os.path.join(defs_dir, task_file)
        log_msg = 'pfile: {0}, task_name: {1}, task_file: {2}, task_file_path: {3}'.\
                  format(pfile, task_name, task_file, task_file_path)
        logger.info(log_msg)
        if os.path.exists(task_file_path):
            clean_file(task_file, task_file_path, logger)
            file_count += 1
        else:
            logger.info('Error! File "%s" not found.', task_file_path)

        pyc_deleted, pycache_file_path = clean_pyc_file(task_name, pycache_dir, defs_dir)
        if pyc_deleted:
            logger.info('Deleted %s', pycache_file_path)
            pyc_file_count += 1
        else:
            logger.info('Unable to find %s', pycache_file_path)
    print('{} files were moved'.format(file_count))
    print('{} pyc files were deleted'.format(pyc_file_count))

def find_pycache_dir(defs_dir):
    """ Find where .pyc files should be stored. """
    pycache_dir = os.path.join(defs_dir, '__pycache__')
    if not (os.path.exists(pycache_dir) and os.path.isdir(pycache_dir)):
        pycache_dir = defs_dir
    return pycache_dir

def get_cla():
    """ Get arguments from the command line. """
    desc = 'Clean out the heasoftpy automagically created files.'
    cl_parser = argparse.ArgumentParser(description=desc)
    dir_help_msg = 'Directory to clean; default: {}.'.format(HEASOFTPY_DIR)
    cl_parser.add_argument('directory', nargs='?',
                           help=dir_help_msg,
                           default=HEASOFTPY_DIR)
    args = cl_parser.parse_args()
    return args

#def get_pyc_filename(py_name, pyc_dir):
#    """ Find .pyc filename corresponding to the file named by py_name """
#    pass

def is_ok_dir(dir_2_check):
    """
    Make sure the directory indicated by dir_2_check exists and is a directory
    """
    # To do: refactor this, cleaning up the unneeded multiple returns.
    msg = ''
    is_ok = True
    if os.path.exists(HOLDING_DIR):
        if not os.path.isdir(dir_2_check):
            is_ok = False
            msg = 'Error! {} exists, but is NOT a directory.'.format(dir_2_check)
    else:
        os.mkdir(dir_2_check)
    return is_ok, msg

def main():
    """ Main function which does the clean up. """

    # Start logging
    log_format = '%(asctime).19s %(message)s'
    logging.basicConfig(filename='heasoftpy_cleanup.log', filemode='w',
                        level=logging.INFO, format=log_format)
    logger = logging.getLogger('heasoftpy cleanup')

    # Get command line arguments
    cl_args = get_cla()
    if str(cl_args.directory) != HEASOFTPY_DIR:
        print('Cleaning directory: {}'.format(str(cl_args.directory)))
        defs_dir = str(cl_args.directory)
    else:
        defs_dir = DEFAULT_DEFS_DIR

    pfiles_list = os.listdir(PFILES_DIR)

    dirs_log_msg = '__file__:   "{0}"\nCUR_DIR:    "{1}"\ndefs_dir:  "{2}"\nPFILES_DIR: "{3}"'\
                   .format(__file__, CUR_DIR, defs_dir, PFILES_DIR)
    logger.info(dirs_log_msg)

    hld_dir_ok, err_msg = is_ok_dir(HOLDING_DIR)
    if not hld_dir_ok:
        sys.exit(err_msg)

    delete_files(defs_dir, pfiles_list, logger)

    return 0

if __name__ == '__main__':
    sys.exit(main())

#2345678901234567890123456789012345678901234567890123456789012345678901234567890
