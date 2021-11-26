
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))


import heasoftpy




if __name__ == '__main__':

    #hsp = heasoftpy.HSPTask('nupipeline')
    #r = hsp(indir='60001111003', outdir='60001111003_p', steminputs='nu60001111003', noprompt=True, verbose=True)
    #hsp = heasoftpy.HSPTask('nicerl2')
    #r = hsp(indir='4693021901', clobber='yes', verbose=False)
    hsp = heasoftpy.HSPTask('fdump')
    r = hsp(infile='tests/test.fits', outfile='STDOUT', columns='-', rows='-', more='yes', 
            prhead='no', stderr=False, verbose=False)
    print('stdout:', r.stdout)
    #print('stderr:', r.stderr)
    #print(r.params)
    #hsp.write_pfile(hsp.pfile, hsp.params, hsp.all_params)
    #hsp(infile='test')
    #print(hsp.all_params)
    #fcn = hsp.generate_fcn_code()
    #with open('heasoftpy/fcn/fdump.py', 'w') as fp: fp.write(fcn)
    #heasoftpy.utils.generate_py_code(['ftlist'])
