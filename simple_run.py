
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))


import heasoftpy




if __name__ == '__main__':

    hsp = heasoftpy.HSPTask('fdump')
    #r = hsp(indir='4693021901', clobber='yes')
    r = hsp(infile='tests/test.fitss', outfile='STDOUT', columns='-', rows='-', more='yes', 
            prhead='yes', stderr=True, verbose=True)
    print('stdout:', r.stdout)
    print('stderr:', r.stderr)
    #print(r.params)
    #hsp.write_pfile(hsp.pfile, hsp.params, hsp.all_params)
    #hsp(infile='test')
    #print(hsp.all_params)
    #fcn = hsp.generate_fcn_code()
    #with open('heasoftpy/fcn/fdump.py', 'w') as fp: fp.write(fcn)
    #heasoftpy.utils.generate_py_code(['ftlist'])
