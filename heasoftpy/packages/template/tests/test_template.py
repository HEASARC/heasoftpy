import unittest
import os

from heasoftpy import template, TemplateTask


class TestPyTasks(unittest.TestCase):
    """Do basic tests for the package structure"""
    
    def test__task_works(self):
        self.assertEqual(1, 1)

    def test__method_works(self):
        self.assertEqual(2, 2)
    
        
if __name__ == '__main__':
    unittest.main()
