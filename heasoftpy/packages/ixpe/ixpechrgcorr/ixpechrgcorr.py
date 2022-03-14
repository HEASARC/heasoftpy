#!/usr/bin/env python


import sys
import heasoftpy as hsp


if __name__ == '__main__':
    task = hsp.ixpe.IXPEchrgcorrTask(name='ixpechrgcorr')
    cmd_args = hsp.utils.process_cmdLine(task)
    result = task(**cmd_args)
    sys.exit(result.returncode)
