
from .context import heasoftpy

import unittest
import os


class TestUtils(unittest.TestCase):
    """Tests for reading parameters"""
    # setUp and tearDown ensures PFILES is restored to what it was
    def setUp(self):
        self.pfiles = os.environ['PFILES']
    
    def tearDown(self):
        os.environ['PFILES'] = self.pfiles

    # temp file; no input to local_pfiles
    def test__utils__local_pfiles_tmpfile(self):
        pDir = heasoftpy.utils.local_pfiles()
        self.assertEqual(pDir[-7:],  '.pfiles')
        self.assertTrue(pDir in os.environ['PFILES'])
        os.rmdir(pDir)
        os.environ['PFILES'] = self.pfiles
    
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
        os.rmdir(pDir)
        os.environ['PFILES'] = self.pfiles
        
    # ensure a task writes to the local pfile created by the user
    def test__utils__local_pfiles_someDir_ensure_write(self):
        pDir = os.path.join('/tmp', str(os.getpid()) + '.tmp')
        oDir = heasoftpy.utils.local_pfiles(pDir)
        heasoftpy.fhelp(task='ftlist')
        self.assertTrue(os.path.exists(f'{pDir}/fhelp.par'))
        os.remove(f'{pDir}/fhelp.par')
        os.rmdir(pDir)
        os.environ['PFILES'] = self.pfiles

        
if __name__ == '__main__':
    unittest.main()
