
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))


import heasoftpy




if __name__ == '__main__':
    #import glob
    #pfiles = glob.glob(os.environ['HEADAS'] + '/syspfiles/*par')
    #for pf in pfiles[-10:]:
    #    pp = heasoftpy.HSPTask.read_pfile(pf)
    #    print(pp);
    #heasoftpy.HSPTask('fcurve', columns='ELV')
    #os.environ['PFILES'] = os.getcwd() + ';' + os.environ['PFILES']
    #hsp = heasoftpy.HSPTask('testtask', infile='IN_FILE')
    #print(hsp.params)
    heasoftpy.tasks.create_fcn('fdump')
    heasoftpy.tasks.fdump()
