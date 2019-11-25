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

HOLDING_DIR = '/tmp/heapy_holding_{}'.format(NOW_STR)
PFILES_DIR = os.path.join(HEADAS_DIR, 'syspfiles')

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

def get_cla():
    """ Get arguments from the command line. """
    cl_parser = argparse.ArgumentParser(description='Clean out the heasoftpy automagically created files.')
    dir_help_msg = 'Directory to clean; default: {}.'.format(HEASOFTPY_DIR)
    cl_parser.add_argument('directory', nargs='?',
                           help=dir_help_msg,
                           default=HEASOFTPY_DIR)
    args = cl_parser.parse_args()
    return args

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

    if os.path.exists(HOLDING_DIR):
        if not os.path.isdir(HOLDING_DIR):
            err_msg = 'Error! {} exists, but is NOT a directory.'.format(HOLDING_DIR)
            sys.exit(err_msg)
    else:
        os.mkdir(HOLDING_DIR)
    # Loop through the par files, deleting the corresponding Python file
    file_count = 0
    pyc_file_count = 0
    for pfile in pfiles_list:
        # rstrip() didn't work below; it removed stuff that should have stayed
        task_name = os.path.basename(pfile).rsplit('.')[0]
        task_file = '.'.join([task_name, 'py'])

        # Since Python doesn't allow a dash ('-') in a function name, the
        # file/function names will have an underscore ('_') where the par file
        # has a  dash.
        task_file_path = os.path.join(defs_dir, task_file.replace('-', '_'))
        log_msg = 'pfile: {0}, task_name: {1}, task_file: {2}, task_file_path: {3}'.\
                  format(pfile, task_name, task_file, task_file_path)
        logger.info(log_msg)
        if os.path.exists(task_file_path):
            clean_file(task_file, task_file_path, logger)
            file_count += 1
        else:
            logger.info('Error! File "%s" not found.', task_file_path)

        pycache_dir = os.path.join(defs_dir, '__pycache__')

        if not (os.path.exists(pycache_dir) and os.path.isdir(pycache_dir)):
            pycache_dir = defs_dir

        pycache_file_path = os.path.join(pycache_dir,
                                         task_file.replace('-', '_') + 'c')
        if os.path.exists(pycache_file_path):
            os.remove(pycache_file_path)
            logger.info('Deleted %s', pycache_file_path)
            pyc_file_count += 1
        else:
            pycache_file_path = os.path.join(defs_dir, '__pycache__',
                                             task_name.replace('-', '_') + '.cpython-36.pyc')
            if os.path.exists(pycache_file_path):
                os.remove(pycache_file_path)
                logger.info('Deleted %s', pycache_file_path)
                pyc_file_count += 1
            else:
                logger.info('Unable to find %s', pycache_file_path)
    print('{} files were moved'.format(file_count))
    print('{} pyc files were deleted'.format(pyc_file_count))
    return 0

if __name__ == '__main__':
    sys.exit(main())

#2345678901234567890123456789012345678901234567890123456789012345678901234567890
