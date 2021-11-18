
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))


import heasoftpy




if __name__ == '__main__':

    hsp = heasoftpy.HSPTask('fdump')
    hsp(infile='test')
    print(hsp.params)
