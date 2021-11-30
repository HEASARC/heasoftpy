
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))


import heasoftpy


if __name__ == '__main__':

    ftlist = heasoftpy.HSPTask('ftlist')
    ftlist.infile = 'tests/test.fits'
    ftlist(option='T', verbose=True)
