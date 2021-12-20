
from .context import heasoftpy

import unittest
import os


class TestUtils(unittest.TestCase):
    """Tests for reading parameters"""

    # temp file; no input to local_pfiles
    def test__utils__local_pfiles_tmpfile(self):
        pDir = heasoftpy.utils.local_pfiles()
        self.assertEqual(pDir, os.path.join('/tmp', str(os.getpid()) + '.pfiles.tmp'))
        self.assertTrue(pDir in os.environ['PFILES'])
        os.rmdir(pDir)
    
    # input is a file not a dir
    def test__utils__local_pfiles_file(self):
        tfile = os.path.join('/tmp', str(os.getpid()) + '.pfiles.tmp')
        with open(tfile, 'w') as fp: fp.write('')
        with self.assertRaises(OSError):
            pDir = heasoftpy.utils.local_pfiles(tfile)
        os.remove(tfile)
    
    # don't have permission
    def test__utils__local_pfiles_permission(self):
        with self.assertRaises(OSError):
            pDir = heasoftpy.utils.local_pfiles('/not-allowed')
    
    # user gives a dir
    def test__utils__local_pfiles_someDir(self):
        pDir = os.path.join('/tmp', str(os.getpid()) + '.tmp')
        oDir = heasoftpy.utils.local_pfiles(pDir)
        self.assertEqual(pDir, oDir)
        self.assertTrue(pDir in os.environ['PFILES'])

        
if __name__ == '__main__':
    unittest.main()
