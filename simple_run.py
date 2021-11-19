
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))


import heasoftpy




if __name__ == '__main__':

    hsp = heasoftpy.HSPTask('fdump')
    hsp(infile='test.fits', outfile='STDOUT', columns='-', rows='-', more='yes', prhead='no')
    hsp.write_pfile(hsp.pfile, hsp.params, hsp.all_params)
    #hsp(infile='test')
    #print(hsp.all_params)
    #fcn = heasoftpy.utils.generate_fcn_code('fdump')
    #with open('heasoftpy/fcn/fdump.py', 'w') as fp: fp.write(fcn)