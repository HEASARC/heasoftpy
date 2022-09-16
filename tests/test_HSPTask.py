
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

    # logfile is a parameter of the task (in addition to being general heasoftpy parameter)
    def test__logfile_in_task_pars(self):
        taskname = 'taskwithlog'
        pfiles = os.environ['PFILES']
        os.environ['PFILES'] = os.getcwd() + ';' + os.environ['PFILES']
        
        # a, q, h, ql, hl
        wTxt = ('par1,s,a,,,,"Par1"\nlogfile,s,h,"NONE",,,"log file"')
        with open(f'{taskname}.par', 'w') as fp: fp.write(wTxt)
        # --- #
        
        hsp  = heasoftpy.HSPTask(taskname)
        
        # no verbose, so logfile for python is ignored
        hsp(par1='IN_FILE', logfile=f'{taskname}.log', do_exec=False)
        self.assertEqual(hsp.logfile, f'{taskname}.log')
        self.assertIsNone(hsp._logfile)
        
        
        # verbose=20 (i.e. request python logging), no py_logfile, we should have {taskname}
        hsp(par1='IN_FILE', logfile=f'{taskname}.log', verbose=20, do_exec=False)
        self.assertEqual(hsp.logfile, f'{taskname}.log')
        self.assertEqual(hsp._logfile, f'{taskname}.log')
        
        # verbose=20 (i.e. request python logging), with py_logfile, we should have py_logfile
        hsp(par1='IN_FILE', logfile=f'{taskname}.log', py_logfile='somelog.log', verbose=20, do_exec=False)
        self.assertEqual(hsp.logfile, f'{taskname}.log')
        self.assertEqual(hsp._logfile, 'somelog.log')
                
        # --- #
        os.environ['PFILES'] = pfiles
        os.remove(f'{taskname}.par')
        
    # task has name as a parameter
    def test__utils__name_is_param(self):
        taskname = 'testtask2'
        
        wTxt = 'infile,s,a,,,,"Name"\nname,s,q,"parname",,,"Name"'
        with open(f'{taskname}.par', 'w') as fp: fp.write(wTxt)
        
        pfiles = os.environ['PFILES']
        os.environ['PFILES'] = os.getcwd() + ';' + os.environ['PFILES']
        
        task = heasoftpy.HSPTask(taskname)
        fcn = task.generate_fcn_code().split('\n')
        for f in fcn:
            if 'HSPTask(name=' in f:
                self.assertIn('name="testtask2"', f)
        
        os.remove(f'{taskname}.par')
        os.environ['PFILES'] = pfiles
        
    
    # a parameter that expected a comma-separated list, given inside quotes.
    # heasoft tasks don't like that
    def test__comma_list_inside_quotes(self):
        task = heasoftpy.HSPTask('fdump')
        res1 = task(infile='tests/test.fits', outfile='STDOUT', columns='"TIME,RATE"', rows='-', more='no', prhead='no')
        self.assertEqual(res1.returncode, 0)
        
if __name__ == '__main__':
    unittest.main()
