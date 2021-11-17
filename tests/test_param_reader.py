
from .context import heasoftpy

import unittest


class TestParReader(unittest.TestCase):
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
            self.assertRaises(heasoftpy.HSPTask.param_type('Text', 'r'), ValueError)
        
        
if __name__ == '__main__':
    unittest.main()
