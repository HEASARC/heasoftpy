
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))


import heasoftpy as hsp
import heasoftpy.packages as hspP


if __name__ == '__main__':

    ftlist = hsp.HSPTask('ftlist')
    r = ftlist(infile='tests/test.fits', option='T', verbose=False)
    print(r)
