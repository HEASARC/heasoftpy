
from .context import heasoftpy

import unittest
import os


class TestParamType(unittest.TestCase):
    """Tests for reading parameters"""

    def test__param_type__b(self):
        test_result = heasoftpy.HSPTask.param_type('', 'b')
        self.assertIsInstance(test_result, bool)

    def test__param_type__f(self):
        test_result = heasoftpy.HSPTask.param_type('', 'f')
        self.assertIsInstance(test_result, str)

    def test__param_type__i(self):
        test_result = heasoftpy.HSPTask.param_type('', 'i')
        self.assertIsInstance(test_result, int)
        
    def test__param_type__r(self):
        test_result = heasoftpy.HSPTask.param_type('', 'r')
        self.assertIsInstance(test_result, float)
        
    def test__param_type__s(self):
        test_result = heasoftpy.HSPTask.param_type('', 's')
        self.assertIsInstance(test_result, str)
        
    def test__param_type__bYes(self):
        test_result = heasoftpy.HSPTask.param_type('yes', 'b')
        self.assertEqual(test_result, True)
        
    def test__param_type__bTrue(self):
        test_result = heasoftpy.HSPTask.param_type('True', 'b')
        self.assertEqual(test_result, True)
        
    def test__param_type__bNo(self):
        test_result = heasoftpy.HSPTask.param_type('no', 'b')
        self.assertEqual(test_result, False)
        
    def test__param_type__bFalse(self):
        test_result = heasoftpy.HSPTask.param_type('False', 'b')
        self.assertEqual(test_result, False)

    def test__param_type__iInt(self):
        test_result = heasoftpy.HSPTask.param_type('42', 'i')
        self.assertEqual(test_result, 42)
        
    def test__param_type__iFloat(self):
        test_result = heasoftpy.HSPTask.param_type('0.42', 'r')
        self.assertEqual(test_result, 0.42)
        
    def test__param_type__sTxt(self):
        test_result = heasoftpy.HSPTask.param_type('a simple text', 's')
        self.assertEqual(test_result, 'a simple text')
    
    def test__param_type__failCast(self):
        with self.assertRaises(ValueError):
            heasoftpy.HSPTask.param_type('Text', 'r')


class TestPFile(unittest.TestCase):
    """Tests for locating pfiles"""

    # HEADAS is not defined
    def test__find_pfile__noHeadas(self):
        headas = os.environ['HEADAS']
        with self.assertRaises(heasoftpy.HSPTaskException):
            del os.environ['HEADAS']
            heasoftpy.HSPTask.find_pfile('test')
        os.environ['HEADAS'] = headas
    
    # task does not exist
    def test__find_pfile__noTask(self):
        with self.assertRaises(heasoftpy.HSPTaskException):
            heasoftpy.HSPTask.find_pfile('noTask')
    
    # user_pfile
    def test__find_pfile__userTrue(self):
        pfile  = heasoftpy.HSPTask.find_pfile('fdump', return_user=True)
        pfile2 = os.path.join(os.environ['PFILES'].split(';')[0], 'fdump.par')
        self.assertEqual(pfile, pfile2)


class TestReadPFile(unittest.TestCase):
    """Tests for reading pfiles"""
    
    # pfile does not exist
    def test__read_pfile__noFile(self):
        with self.assertRaises(IOError):
            heasoftpy.HSPTask.read_pfile('/dir/to/noTask')
            
    # simple .par file
    def test__find_pfile__simpleFile(self):
        wTxt = 'infile,s,a,,,,"Name of file"'
        tmpfile = 'tmp.simpleFile.par'
        open(tmpfile, 'w').write(wTxt)
        pars = dict(heasoftpy.HSPTask.read_pfile(tmpfile))
        expected = {'infile': {'type':'s', 'mode':'a', 'default':'',
                               'min': '', 'max': '', 'prompt': 'Name of file'}}
        self.assertEqual(pars, expected)
        os.remove(tmpfile)
        
if __name__ == '__main__':
    unittest.main()
