
from .context import heasoftpy

import unittest
import os


class TestHSPTask(unittest.TestCase):
    """Tests for initializing HSPTask object"""

    @classmethod
    def setUpClass(cls):
        """Create simple .par file for testing"""
        cls.taskname = 'testtask'
        
        wTxt = 'infile,s,a,,,,"Name"\nnumber,r,q,2.0,,,"Fraction"'
        with open(f'{cls.taskname}.par', 'w') as fp: fp.write(wTxt)
        
        cls.pfiles = os.environ['PFILES']
        os.environ['PFILES'] = os.getcwd() + ';' + os.environ['PFILES']
        
    @classmethod
    def tearDownClass(cls):
        os.remove(f'{cls.taskname}.par')
        os.environ['PFILES'] = cls.pfiles
    
    
    # no name given -> fail
    def test__init_HSPTask__noName(self):
        with self.assertRaises(heasoftpy.HSPTaskException):
            heasoftpy.HSPTask()

    # case: initilize by kwargs
    def test__init_HSPTask__kwargs(self):
        hsp  = heasoftpy.HSPTask(self.taskname)
        hsp(infile='IN_FILE', number=4, do_exec=False)
        self.assertEqual(hsp.params['infile'], 'IN_FILE')
        self.assertEqual(hsp.params['number'], 4)
    
    # case: initilize by another HSPTask object
    def test__init_HSPTask__anotherHSPTask(self):
        hsp  = heasoftpy.HSPTask(self.taskname)
        hsp(infile='IN_FILE', number=4, do_exec=False)
        hsp2 = heasoftpy.HSPTask(self.taskname)
        hsp2(hsp, do_exec=False)
        self.assertEqual(hsp.params, hsp2.params)
    
    # case: initilize by dict
    def test__init_HSPTask__dict(self):
        hsp  = heasoftpy.HSPTask(self.taskname)
        hsp({'number':4, 'infile':'IN_FILE'}, do_exec=False)
        self.assertEqual(hsp.params['infile'], 'IN_FILE')
        self.assertEqual(hsp.params['number'], 4)
        
    # case: query one parameter
    def test__init_HSPTask__query1(self):
        # the following is a work-around to simulate user input
        orig_input_f = __builtins__['input']
        __builtins__['input'] = lambda _: 5.0
        hsp  = heasoftpy.HSPTask(self.taskname)
        hsp(infile='IN_FILE', do_exec=False)
        self.assertEqual(hsp.params['infile'], 'IN_FILE')
        self.assertEqual(hsp.params['number'], 5.0)
        __builtins__['input'] = orig_input_f
    
    # required parameter not given
    def test__init_HSPTask__qnotgiven(self):
        # the following is a work-around to simulate user input
        orig_input_f = __builtins__['input']
        with self.assertRaises(ValueError):
            def dummyf(_): raise ValueError
            __builtins__['input'] = dummyf
            hsp  = heasoftpy.HSPTask(self.taskname)
            hsp(infile='IN_FILE', do_exec=False)
        __builtins__['input'] = orig_input_f
        
    # case: fill params by hand
    def test__init_HSPTask__dict(self):
        hsp  = heasoftpy.HSPTask(self.taskname)
        hsp.infile = 'INFILE'
        hsp.number = 7
        self.assertEqual(hsp.params['infile'], 'INFILE')
        self.assertEqual(hsp.params['number'], 7)
    
    # case: fill params by hand; wrong type
    def test__init_HSPTask__dict(self):
        hsp  = heasoftpy.HSPTask(self.taskname)
        with self.assertRaises(ValueError):
            hsp.number = 'wrong_type'
            
    # check we have mode even if absent from par file
    def test__init_HSPTask__absent_mode(self):
        hsp  = heasoftpy.HSPTask(self.taskname)
        self.assertIn('mode', hsp.par_names)
    
    
    # keyword params take priority over inline params
    def test__init_HSPTask__keyword_priority(self):
        hsp  = heasoftpy.HSPTask(self.taskname)
        hsp.infile = 'infile-1'
        res = hsp(infile='infile-2', number=4, do_exec=False)
        self.assertEqual(hsp.params['infile'], 'infile-2')
        
    # raise error if HSPTask given the wrong name
    def test__init_HSPTask__wrong_taskname(self):
        class HSP(heasoftpy.HSPTask):
            name = 'name-1'
        with self.assertRaises(heasoftpy.HSPTaskException):
            hsp = HSP('wrong-name')
        
if __name__ == '__main__':
    unittest.main()