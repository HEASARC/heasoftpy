#!/usr/bin/env python

""" Tests of heasoftpy """

#import importlib
import os
import re
import sys
import unittest

CUR_FILE_DIR = os.path.dirname(os.path.abspath(__file__))
DIR_PARTS = CUR_FILE_DIR.split(os.sep)
PACKAGE_DIR = os.sep.join(DIR_PARTS[:-2])

try:
    import heasoftpy
    import heasoftpy.core.result
except ModuleNotFoundError:
    # A kludge to get the import to work, assuming the heasoftpy directory is
    # one level above the test directory.
    sys.path.append(PACKAGE_DIR)
    import heasoftpy
    import heasoftpy.core.result

# Define constants for expected outputs here to keep the tests cleaner.
# This is not in the setUp method because that runs for every test
# and these results are specific to a test or set of tests.
FTLIST_EXP_OUT = """
        Name               Type       Dimensions
        ----               ----       ----------
HDU 1   Primary Array      Null Array                               
HDU 2   RATE               BinTable     3 cols x 5371 rows          
"""

FTSTAT_EXP_STR = """^=* statistics for .*test_rate\.fit =*

TIME\[d\]:
   min:       [+-]??\d*\.\d*
   max:       [+-]??\d*\.\d*
  mean:       [+-]??\d*\.\d*
median:       [+-]??\d*\.\d*
 sigma:       [+-]??\d*\.\d*
   sum:       [+-]??\d*\.\d*
  mode:       [+-]??\d*\.\d*
 modes:          \d*
 modez:          \d*
  good:       \d*
  null:       \d*

RATE\[counts\/s\]:
   min:       [+-]??\d*\.\d*
   max:       [+-]??\d*\.\d*
  mean:       [+-]??\d*\.\d*
median:       [+-]??\d*\.\d*
 sigma:       [+-]??\d*\.\d*
   sum:       [+-]??\d*
  mode:       [+-]??\d*\.\d*
 modes:         \d*
 modez:         \d*
  good:       \d*
  null:       \d*

ERROR\[counts\/s\]:
   min:       [+-]*\d*\.\d*
   max:       [+-]*\d*\.\d*
  mean:       [+-]*\d*\.\d*
median:       [+-]*\d*\.\d*
 sigma:       [+-]*\d*\.\d*
   sum:       [+-]*\d*\.\d*
  mode:       [+-]*\d*\.\d*
 modes:         \d*
 modez:         \d*
  good:       \d*
  null:       \d*
"""

FTSTAT_EXP_PATTERN = re.compile(FTSTAT_EXP_STR, re.DOTALL)


FTVERIFY_EXP_STR = """
\s*ftverify \d\.\d\d \(CFITSIO V\d\.\d\d\d\)               
               ------------------------------               
 
HEASARC conventions are being checked.
 
File: .*test_rate.fit.*\d Header-Data Units in this file\..* 
"""

holder="""
=================== HDU 1: Primary Array ===================
 
 \d* header keywords
 
 Null data array; NAXIS = \d* 
 
=================== HDU 2: BINARY Table ====================
 
 \d* header keywords
 
 RATE  \(\d* columns x \d* rows\)
 
 Col# Name \(Units\)       Format
   1 TIME \(d\)             D         
   2 RATE \(counts\/s\)      E.*
   3 ERROR \(counts\/s\)     E.*
\+* Error Summary  \+*
 
 HDU#  Name \(version\)       Type             Warnings  Errors
 1                          Primary Array    0         0     
 2     RATE                 Binary Table     0         0     
 
\** Verification found 0 warning\(s\) and 0 error\(s\)\. \**.*
"""

FTVERIFY_EXP_PATTERN = re.compile(FTVERIFY_EXP_STR, re.DOTALL)

#def make_function(func_name):
#    """ Utility function for creating function files. """
#    #func_text = create_function.create_function(func_name)
#    with open(func_name + '.py', 'wt') as func_file:
#        func_file.write(func_text)

class TestTasks(unittest.TestCase):
    """
    Class for testing HEASoft tasks/program when called via the Python interface.
    """

    def setUp(self):
        
        self.test_filename = 'test_rate.fit'
        self.test_filepath = os.path.join(PACKAGE_DIR, 'heasoftpy', 'tests', self.test_filename)
        self.maxDiff = 1000


    ftv_out = """ 
               ftverify 4.20 (CFITSIO V3.480)               
               ------------------------------               
 
HEASARC conventions are being checked.
 
File: test_rate.fit

2 Header-Data Units in this file.
 
=================== HDU 1: Primary Array ===================
 
 29 header keywords
 
 Null data array; NAXIS = 0 
 
=================== HDU 2: BINARY Table ====================
 
 52 header keywords
 
 RATE  (3 columns x 5371 rows)
 
 Col# Name (Units)       Format
   1 TIME (d)             D         
   2 RATE (counts/s)      E         
   3 ERROR (counts/s)     E         
 
++++++++++++++++++++++ Error Summary  ++++++++++++++++++++++
 
 HDU#  Name (version)       Type             Warnings  Errors
 1                          Primary Array    0         0     
 2     RATE                 Binary Table     0         0     
 
**** Verification found 0 warning(s) and 0 error(s). ****

"""

#    @unittest.skip('skipping test_A')
#    def test_A(self):
#        print('in test_A: ', re.match(FTVERIFY_EXP_OUT, self.ftv_out))
#        self.assertRegex(self.ftv_out, FTVERIFY_EXP_OUT)

    def tearDown(self):
        """ Currently a placeholder """
        #pass

#    @unittest.skip('skipping fhelp')
    def test_fhelp(self):
        """
        Test the fthelp program by retrieving the help for ftlist.
        """
        help_out = heasoftpy.fhelp(task='ftlist')
        #string_out = byte_out.decode()
        test_out = []
        for test_line in help_out.stdout.split('\n'):
            test_out.append(test_line)
        self.assertTrue(test_out[0].strip() == 'NAME' and test_out[1].strip() == '' and
                        test_out[2].strip() == 'ftlist - List the contents of the input file.')

#    @unittest.skip('skipping fhelp_pos_arg')
    def test_fhelp_pos_arg(self):
        """
        Test the fthelp program by retrieving the help for ftlist.
        """
        help_out = heasoftpy.fhelp('ftlist')
        #string_out = byte_out.decode()
        test_out = []
        for test_line in help_out.stdout.split('\n'):
            test_out.append(test_line)
        self.assertTrue(test_out[0].strip() == 'NAME' and test_out[1].strip() == '' and
                        test_out[2].strip() == 'ftlist - List the contents of the input file.')

    def test_ftcopy(self):
        """
        Test the ftcopy program by copying the test file to a new file
        named "copy_of_NAMEOFTESTFILE." Note that the file will be deleted
        when the test run is finished.
        """
        copy_name = os.path.join(PACKAGE_DIR, 'heasoftpy', 'tests', 'copy_of_' + self.test_filename)

        # Delete file if it already exists
        if os.path.exists(copy_name):
            os.remove(copy_name)

        heasoftpy.ftcopy(infile=self.test_filepath, outfile=copy_name)
        #print(test_out)
        self.assertTrue(os.path.exists(copy_name))

#    @unittest.skip('skipping fthelp')
    def test_fthelp(self):
        """
        Test the fthelp program by retrieving the help for ftlist.
        """
        help_out = heasoftpy.fthelp(task='ftlist')
        #string_out = byte_out.decode()
        test_out = []
        for test_line in help_out.stdout.split('\n'):
            test_out.append(test_line)
        self.assertTrue(test_out[0].strip() == 'NAME' and test_out[1].strip() == '' and
                        test_out[2].strip() == 'ftlist - List the contents of the input file.')

#    @unittest.skip('skipping ftlist')
    def test_ftlist(self):
        """ Test the ftlist program """
        test_out = heasoftpy.ftlist(infile=self.test_filepath, option='H').stdout
        self.assertEqual(test_out, FTLIST_EXP_OUT)

#    @unittest.skip('skipping ftlist_dot_output')
    def test_ftlist_dot_output(self):
        """ Test the ftlist program """
        test_out = heasoftpy.ftlist(infile=self.test_filepath, option='H').output
        self.assertEqual(test_out, FTLIST_EXP_OUT.split('\n'))

    #@unittest.skip('skipping ftstat')
    def test_ftstat(self):
        """ Test the ftlist program """
        test_out = heasoftpy.ftstat(infile=self.test_filepath, min=0, max=0,
                                    mean=0, median=0, sigma=0, sum=0,
                                    xmin=0, ymin=0, xmax=0, ymax=0,
                                    xcent=0, ycent=0, xsigma=0, ysigma=0,
                                    good=0, null=0, clipped=0,
                                    modev=0, modes=0, modez=0).stdout
        self.assertRegex(test_out, FTSTAT_EXP_PATTERN)

    # Need to figure out why the assertRegex fails
    #@unittest.skip('Skipping ftverify')
    def test_ftverify(self):
        """ Tests the ftverify program """
#        print('\nEntering test_ftverify\n')
        # It seems we need to give the specific and full path here
        test_result = heasoftpy.ftverify(infile=self.test_filepath,
                                         numerrs=0, numwrns=0,
                                         stderr=True)
#        test_result = heasoftpy.ftverify(self.test_filepath, stderr=True)
                                         
        test_out = test_result.stdout
        test_err = test_result.stderr
        if isinstance(test_out, bytes):
            test_out = test_out.decode()
#        print('\ntest_out\n-----\n{}\n-----\n'.format(test_out))
        if isinstance(test_err, bytes):
            test_err = test_err.decode()
        self.assertRegex(test_out, FTVERIFY_EXP_PATTERN)
#        print('\nExitng test_ftverify\n')

    # Need to figure out why the assertRegex fails
    #@unittest.skip('Skipping ftverify_single_arg')
    def test_ftverify_single_arg(self):
        """ Tests the ftverify program using only one (positional) argument"""
        test_result = heasoftpy.ftverify(self.test_filepath, stderr=True)
        test_out = test_result.stdout
        with open('ftverify_single.out', 'wt') as mfile:
            mfile.write(test_out)
        test_err = test_result.stderr
        if isinstance(test_out, bytes):
            test_out = test_out.decode()
        if isinstance(test_err, bytes):
            test_err = test_err.decode()
        self.assertRegex(test_out, FTVERIFY_EXP_PATTERN)

if __name__ == '__main__':
    unittest.main()
