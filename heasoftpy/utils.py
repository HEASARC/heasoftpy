import sys
import os
import subprocess
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
        
    return args