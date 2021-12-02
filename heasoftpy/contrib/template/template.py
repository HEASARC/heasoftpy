#!/usr/bin/env python


import sys
import heasoftpy as hsp
import heasoftpy.contrib as hspContrib


if __name__ == '__main__':
    
    task = hspContrib.TemplateTask(name='template')
    cmd_args = hsp.utils.process_cmdLine(task)
    result = task(**cmd_args)
    sys.exit(result.returncode)