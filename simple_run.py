
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))


import heasoftpy




if __name__ == '__main__':
    import glob
    pfiles = glob.glob(os.environ['HEADAS'] + '/syspfiles/*par')
    for pf in pfiles[-10:]:
        pp = HSPTask.read_pfile(pf)
        print(pp);