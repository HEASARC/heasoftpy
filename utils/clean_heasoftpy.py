#!/usr/bin/env python

"""
Removes Python files that correspond to the HEASOFT parameter files and which
were (most likely) created by the heasoftpy.__init__.
"""

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

#HEASOFTPY_DIR = os.path.join(CUR_DIR, 'write_fns') # from comparison vs "onthefly"

HOLDING_DIR = '/tmp/heapy_holding_{}'.format(NOW_STR)
PFILES_DIR = os.path.join(HEADAS_DIR, 'syspfiles')

#2345678901234567890123456789012345678901234567890123456789012345678901234567890
def main():
    """ Main function which does the clean up. """
    log_format = '%(asctime).19s %(message)s'
    logging.basicConfig(filename='heasoftpy_cleanup.log', filemode='w', 
                        level=logging.INFO, format=log_format)
    logger = logging.getLogger('heasoftpy cleanup')
    pfiles_list = os.listdir(PFILES_DIR)
    print('__file__:   "{0}"\nCUR_DIR:    "{1}"\nHEASOFTPY_DIR:  "{2}"\nPFILES_DIR: "{3}"'\
          .format(__file__, CUR_DIR, HEASOFTPY_DIR, PFILES_DIR))

    if os.path.exists(HOLDING_DIR):
        if not os.path.isdir(HOLDING_DIR):
            err_msg = 'Error! {} exists, but is NOT a directory.'.format(HOLDING_DIR)
            sys.exit(err_msg)
    else:
        os.mkdir(HOLDING_DIR)
    # Loop through the par files, deleting the corresponding Python file
    file_count = 0
    for pfile in pfiles_list:
        # rstrip() didn't work below; it removed stuff that should have stayed
        task_name = os.path.basename(pfile).rsplit('.')[0]
        task_file = '.'.join([task_name, 'py'])
        # Since Python doesn't allow a dash ('-') in a function name, the
        # file/function names will have an underscore ('_') where the par file
        # has a  dash.
        task_file_path = os.path.join(HEASOFTPY_DIR, task_file.replace('-', '_'))
        log_msg = 'pfile: {0}, task_name: {1}, task_file: {2}, task_file_path: {3}'.\
                  format(pfile, task_name, task_file, task_file_path)
        logger.info(log_msg)
        if os.path.exists(task_file_path):
            dest_path = os.path.join(HOLDING_DIR, task_file)
            logger.info('Copying {} to holding area in /tmp'.format(task_file_path))
            shutil.copyfile(task_file_path, dest_path)
            logger.info('Removing {}.'.format(task_file_path))
            os.remove(task_file_path)
            file_count += 1
        else:
            logger.info('Error! File "{}" not found.'.format(task_file_path))
    print('{} files were moved'.format(file_count))
    return 0

if __name__ == '__main__':
    sys.exit(main())
