
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))


import heasoftpy as hsp
from heasoftpy import contrib as hspC


if __name__ == '__main__':

    ftlist = hsp.HSPTask('ftlist')
    r = ftlist(infile='tests/test.fits', option='T', verbose=False)
    print(r)
