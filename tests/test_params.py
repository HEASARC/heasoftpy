
from .context import heasoftpy

import unittest
import os
import re


class TestParamType(unittest.TestCase):
    """Tests for reading parameters"""

    def test__param_type__b(self):
        # this is a yes/no string
        test_result = heasoftpy.HSPParam.param_type('', 'b')
        self.assertIsInstance(test_result, str)

    def test__param_type__f(self):
        test_result = heasoftpy.HSPParam.param_type('', 'f')
        self.assertIsInstance(test_result, str)

    def test__param_type__i(self):
        test_result = heasoftpy.HSPParam.param_type('', 'i')
        self.assertIsInstance(test_result, int)
        
    def test__param_type__r(self):
        test_result = heasoftpy.HSPParam.param_type('', 'r')
        self.assertIsInstance(test_result, float)
    
    def test__param_type__r_INDEF(self):
        test_result = heasoftpy.HSPParam.param_type('INDEF', 'r')
        self.assertEqual(test_result, 'INDEF')
        
    def test__param_type__s(self):
        test_result = heasoftpy.HSPParam.param_type('', 's')
        self.assertIsInstance(test_result, str)
        
    def test__param_type__bYes(self):
        test_result = heasoftpy.HSPParam.param_type('yes', 'b')
        self.assertEqual(test_result, 'yes')
        
    def test__param_type__bTrue(self):
        test_result = heasoftpy.HSPParam.param_type('True', 'b')
        self.assertEqual(test_result, 'yes')
        
    def test__param_type__bNo(self):
        test_result = heasoftpy.HSPParam.param_type('no', 'b')
        self.assertEqual(test_result, 'no')
        
    def test__param_type__bFalse(self):
        test_result = heasoftpy.HSPParam.param_type('False', 'b')
        self.assertEqual(test_result, 'no')

    def test__param_type__iInt(self):
        test_result = heasoftpy.HSPParam.param_type('42', 'i')
        self.assertEqual(test_result, 42)
        
    def test__param_type__iFloat(self):
        test_result = heasoftpy.HSPParam.param_type('0.42', 'r')
        self.assertEqual(test_result, 0.42)
        
    def test__param_type__sTxt(self):
        test_result = heasoftpy.HSPParam.param_type('a simple text', 's')
        self.assertEqual(test_result, 'a simple text')
    
    def test__param_type__failCast(self):
        with self.assertRaises(ValueError):
            heasoftpy.HSPParam.param_type('Text', 'r')


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
        pfile2 = os.path.join(re.split(';|:', os.environ['PFILES'])[0], 'fdump.par')
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
        with open(tmpfile, 'w') as fp: fp.write(wTxt)
        pars = heasoftpy.HSPTask.read_pfile(tmpfile)
        self.assertEqual(pars[0].pname, 'infile')
        self.assertEqual(pars[0].type, 's')
        self.assertEqual(pars[0].mode, 'a')
        self.assertEqual(pars[0].default, '')
        self.assertEqual(pars[0].min, '')
        self.assertEqual(pars[0].max, '')
        self.assertEqual(pars[0].prompt, 'Name of file')
        os.remove(tmpfile)

    # input has commas
    def test__read_pfile__par_with_comma(self):
        wTxt = 'filtlist,s,a,"val1,val2",,,"Name of file, and stuff"'
        tmpfile = 'tmp.simpleFile.par'
        with open(tmpfile, 'w') as fp: fp.write(wTxt)
        pars = heasoftpy.HSPTask.read_pfile(tmpfile)
        self.assertEqual(pars[0].pname, 'filtlist')
        self.assertEqual(pars[0].default, 'val1,val2')
        self.assertEqual(pars[0].prompt, 'Name of file, and stuff')
        os.remove(tmpfile)
    
    # prompt text has unclosed quotes
    def test__read_pfile__prompt_with_unclosed_quotes(self):
        wTxt = 'filtlist,s,a,val1,,,"Name of file, and stuff'
        tmpfile = 'tmp.simpleFile.par'
        with open(tmpfile, 'w') as fp: fp.write(wTxt)
        pars = heasoftpy.HSPTask.read_pfile(tmpfile)
        self.assertEqual(pars[0].pname, 'filtlist')
        self.assertEqual(pars[0].prompt, 'Name of file, and stuff')
        os.remove(tmpfile)
        
class TestWritePFile(unittest.TestCase):
    """Tests for write_pfile"""
    
        
    # test:mode=q.
    def test__write_pfile__mode_q(self):
        taskname = 'testtask'
        pfiles = os.environ['PFILES']
        sep = ':' if ';' in os.environ["PFILES"] else ';'
        os.environ['PFILES'] = os.getcwd() + sep + os.environ['PFILES']
        
        # a, q, h, ql, hl
        wTxt = ('par1,s,a,,,,"Par1"\npar2,r,q,2.0,,,"Par2"\npar3,r,h,3.0,,,"Par3"\n'
                'par4,r,ql,4.0,,,"Par4"\npar5,r,hl,5.0,,,"Par5"\nmode,s,h,"q",,,')
        with open(f'{taskname}.par', 'w') as fp: fp.write(wTxt)
        # --- #
        
        hsp  = heasoftpy.HSPTask(taskname)
        hsp(par1='IN_FILE', par2=200, par3=300, par4=400, par5=500, do_exec=False)
        tmpfile = f'{taskname}.2.par'
        hsp.write_pfile(tmpfile)
        newpars = heasoftpy.HSPTask.read_pfile(tmpfile)
        
        # a: mode:q; no write
        self.assertEqual(newpars[0].value, '')
        
        # q: mode:q; no write
        self.assertEqual(newpars[1].value, 2.0)
        
        # h: mode:q; no write
        self.assertEqual(newpars[2].value, 3.0)
        
        # ql: mode:q; write
        self.assertEqual(newpars[3].value, 400)
        
        # hl: mode:q; write
        self.assertEqual(newpars[4].value, 500)

        os.remove(tmpfile)
        
        # --- #
        os.environ['PFILES'] = pfiles
        os.remove(f'{taskname}.par')

        
    # test:mode=ql.
    def test__write_pfile__mode_ql(self):
        taskname = 'testtask'
        pfiles = os.environ['PFILES']
        sep = ':' if ';' in os.environ["PFILES"] else ';'
        os.environ['PFILES'] = os.getcwd() + sep + os.environ['PFILES']
        
        # a, q, h, ql, hl
        wTxt = ('par1,s,a,,,,"Par1"\npar2,r,q,2.0,,,"Par2"\npar3,r,h,3.0,,,"Par3"\n'
                'par4,r,ql,4.0,,,"Par4"\npar5,r,hl,5.0,,,"Par5"\nmode,s,h,"ql",,,')
        with open(f'{taskname}.par', 'w') as fp: fp.write(wTxt)
        # --- #
        
        hsp  = heasoftpy.HSPTask(taskname)
        hsp(par1='IN_FILE', par2=200, par3=300, par4=400, par5=500, do_exec=False)
        tmpfile = f'{taskname}.2.par'
        hsp.write_pfile(tmpfile)
        newpars = heasoftpy.HSPTask.read_pfile(tmpfile)
        
        # a: mode:ql; write
        self.assertEqual(newpars[0].value, 'IN_FILE')
        
        # q: mode:ql; no write
        self.assertEqual(newpars[1].value, 2.0)
        
        # h: mode:ql; no write
        self.assertEqual(newpars[2].value, 3.0)
        
        # ql: mode:ql; write
        self.assertEqual(newpars[3].value, 400)
        
        # hl: mode:ql; write
        self.assertEqual(newpars[4].value, 500)

        os.remove(tmpfile)
        
        # --- #
        os.environ['PFILES'] = pfiles
        os.remove(f'{taskname}.par')
        
        
    # test:mode=h.
    def test__write_pfile__mode_h(self):
        taskname = 'testtask'
        pfiles = os.environ['PFILES']
        sep = ':' if ';' in os.environ["PFILES"] else ';'
        os.environ['PFILES'] = os.getcwd() + sep + os.environ['PFILES']
        
        # a, q, h, ql, hl
        wTxt = ('par1,s,a,,,,"Par1"\npar2,r,q,2.0,,,"Par2"\npar3,r,h,3.0,,,"Par3"\n'
                'par4,r,ql,4.0,,,"Par4"\npar5,r,hl,5.0,,,"Par5"\nmode,s,h,"h",,,')
        with open(f'{taskname}.par', 'w') as fp: fp.write(wTxt)
        # --- #
        
        hsp  = heasoftpy.HSPTask(taskname)
        hsp(par1='IN_FILE', par2=200, par3=300, par4=400, par5=500, do_exec=False)
        tmpfile = f'{taskname}.2.par'
        hsp.write_pfile(tmpfile)
        newpars = heasoftpy.HSPTask.read_pfile(tmpfile)
        
        # a: mode:h; no write
        self.assertEqual(newpars[0].value, '')
        
        # q: mode:h; no write
        self.assertEqual(newpars[1].value, 2.0)
        
        # h: mode:h; no write
        self.assertEqual(newpars[2].value, 3.0)
        
        # ql: mode:h; write
        self.assertEqual(newpars[3].value, 400)
        
        # hl: mode:h; write
        self.assertEqual(newpars[4].value, 500)

        os.remove(tmpfile)
        
        # --- #
        os.environ['PFILES'] = pfiles
        os.remove(f'{taskname}.par')
        
        
    # test:mode=hl.
    def test__write_pfile__mode_hl(self):
        taskname = 'testtask'
        pfiles = os.environ['PFILES']
        sep = ':' if ';' in os.environ["PFILES"] else ';'
        os.environ['PFILES'] = os.getcwd() + sep + os.environ['PFILES']
        
        # a, q, h, ql, hl
        wTxt = ('par1,s,a,,,,"Par1"\npar2,r,q,2.0,,,"Par2"\npar3,r,h,3.0,,,"Par3"\n'
                'par4,r,ql,4.0,,,"Par4"\npar5,r,hl,5.0,,,"Par5"\nmode,s,h,"hl",,,')
        with open(f'{taskname}.par', 'w') as fp: fp.write(wTxt)
        # --- #
        
        hsp  = heasoftpy.HSPTask(taskname)
        hsp(par1='IN_FILE', par2=200, par3=300, par4=400, par5=500, do_exec=False)
        tmpfile = f'{taskname}.2.par'
        hsp.write_pfile(tmpfile)
        newpars = heasoftpy.HSPTask.read_pfile(tmpfile)
        
        # a: mode:h; write
        self.assertEqual(newpars[0].value, 'IN_FILE')
        
        # q: mode:h; no write
        self.assertEqual(newpars[1].value, 2.0)
        
        # h: mode:h; no write
        self.assertEqual(newpars[2].value, 3.0)
        
        # ql: mode:h; write
        self.assertEqual(newpars[3].value, 400)
        
        # hl: mode:h; write
        self.assertEqual(newpars[4].value, 500)

        os.remove(tmpfile)
        
        # --- #
        os.environ['PFILES'] = pfiles
        os.remove(f'{taskname}.par')
        
        

class TestParamExtra(unittest.TestCase):
    """Some additional tests for handling parameters"""
    
    # a parameter that expects a comma-separated list, given inside quotes.
    # heasoft tasks don't like that
    def test__comma_list_inside_quotes(self):
        task = heasoftpy.HSPTask('fdump')
        res1 = task(infile='tests/test.fits', outfile='STDOUT', columns='"TIME,RATE"', rows='-', more='no', prhead='no')
        self.assertEqual(res1.returncode, 0)

        
if __name__ == '__main__':
    unittest.main()
