
from .context import heasoftpy

import unittest
import os


class TestPyTasks(unittest.TestCase):
    """Test a few tasks using the python interface"""
    
    
    def test__tasks__fhelp(self):
        task = heasoftpy.HSPTask('fhelp')
        result = task(task='ftlist')
        out = result.stdout.split('\n')
        self.assertEqual(out[0], 'NAME')
        self.assertEqual(out[2], '   ftlist - List the contents of the input file.')
        self.assertEqual(out[6], '   ftlist infile[ext][filters] option')
    
    
    def test__tasks__flistH(self):
        task = heasoftpy.HSPTask('ftlist')
        result = task(infile='tests/test.fits', option='H', outfile='-')
        out = result.stdout.split('\n')
        self.assertEqual(out[4], 'HDU 2   RATE               BinTable     3 cols x 10 rows            ')
    
    
    def test__tasks__flistC(self):
        task = heasoftpy.HSPTask('ftlist')
        result = task(infile='tests/test.fits', option='C', outfile='-')
        out = result.stdout.split('\n')
        self.assertEqual(out[3], '    1 TIME               D [d]                label for field   1')
        self.assertEqual(out[4], '    2 RATE               E [counts/s]         label for field   8')
        self.assertEqual(out[5], '    3 ERROR              E [counts/s]         label for field   9')
    
    
    def test__tasks__flistT(self):
        task = heasoftpy.HSPTask('ftlist')
        result = task(infile='tests/test.fits', option='T', colheader='no', rownum='no', separator=" ", outfile='-')
        out = result.stdout.split('\n')
        self.assertEqual(out[0], '       1164.29445392592        18.2019        1.22564')
        self.assertEqual(out[1], '       1164.43056492592        16.3479        1.38458')
        self.assertEqual(out[2], '       1164.43167642593        17.2304        1.48210')
        
        
    def test__tasks__fdump(self):
        task = heasoftpy.HSPTask('fdump')
        result = task(infile='tests/test.fits', outfile='STDOUT', columns='-', rows='-', more='no', prhead='yes')
        out = result.stdout.split('\n')
        self.assertEqual(out[0], 'SIMPLE  =                    T / file does conform to FITS standard')
        self.assertEqual(out[1], 'BITPIX  =                    8 / number of bits per data pixel')
        self.assertEqual(out[2], 'NAXIS   =                    0 / number of data axes')
    
    
    def test__tasks__fdump2runs(self):
        task = heasoftpy.HSPTask('fdump')
        res1 = task(infile='tests/test.fits', outfile='STDOUT', columns='-', rows='-', more='no', prhead='yes')
        res2 = task(infile='tests/test.fits', outfile='STDOUT', columns='-', rows='-', more='no', prhead='yes')
        self.assertEqual(res1.params, res2.params)
        
    # re-read pfile after a task is run
    def test__write_pfile__fstruct_rereadPfile(self):
        task = heasoftpy.HSPTask('fstruct')
        # we force isfits=no, which should be updated after running the task
        res  = task(infile='tests/test.fits', isfits='no')
        self.assertEqual(task.isfits.value, 'yes')

        
    # re-read pfile, ensure HSPTask.params match HSPResult.params
    def test__write_pfile__fstruct_rereadPfile_updateHSPResult(self):
        task = heasoftpy.HSPTask('fstruct')
        # we force isfits=no, which should be updated after running the task
        res  = task(infile='tests/test.fits', isfits='no')
        self.assertEqual(task.isfits.value, res.params['isfits'])
        
        
    # make sure returncode is not None when verbose=True
    def test__tasks__returncode_w_verbose(self):
        task = heasoftpy.HSPTask('ftlist')
        result = task(infile='tests/test.fits', option='C', outfile='-', verbose=True)
        self.assertIsNotNone(result.returncode)
        
    # ensure True/False are converted to yes/not in bool params
    def test__tasks__boolParam_conversion(self):
        task = heasoftpy.HSPTask('ftlist')
        res1 = task(infile='tests/test.fits', option='T', colheader=False, rownum=True, separator=" ", outfile='-')
        res2 = task(infile='tests/test.fits', option='T', colheader='no', rownum='yes', separator=" ", outfile='-')
        self.assertEqual(res1.stdout, res2.stdout)
        
if __name__ == '__main__':
    unittest.main()
