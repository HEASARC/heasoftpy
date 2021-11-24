
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
        result = task(infile='tests/test.fits', option='H')
        out = result.stdout.split('\n')
        self.assertEqual(out[4], 'HDU 2   RATE               BinTable     3 cols x 10 rows            ')
    
    
    def test__tasks__flistC(self):
        task = heasoftpy.HSPTask('ftlist')
        result = task(infile='tests/test.fits', option='C')
        out = result.stdout.split('\n')
        self.assertEqual(out[3], '    1 TIME               D [d]                label for field   1')
        self.assertEqual(out[4], '    2 RATE               E [counts/s]         label for field   8')
        self.assertEqual(out[5], '    3 ERROR              E [counts/s]         label for field   9')
        
    def test__tasks__flistC(self):
        task = heasoftpy.HSPTask('ftlist')
        result = task(infile='tests/test.fits', option='T', colheader='no', rownum='no', separator=" ")
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
        
if __name__ == '__main__':
    unittest.main()
