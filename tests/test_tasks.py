#!/usr/bin/env python

""" Tests of heasoftpy """

#import importlib
import os
import re
import sys
import unittest

try:
    import heasoftpy
    import heasoftpy.core.result
except ModuleNotFoundError:
    # A kludge to get the import to work, assuming the heasoftpy directory is
    # one level above the test directory.
    cur_file_dir = os.path.dirname(os.path.abspath(__file__))
    dir_parts = cur_file_dir.split(os.sep)
    PACKAGE_DIR = os.sep.join(dir_parts[:-2])
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

FTVERIFY_EXP_OUT = """^\s*ftverify \d\.\d\d \(CFITSIO V\d\.\d\d\d\)               
               ------------------------------               
 
HEASARC conventions are being checked.
 
File: my_rate.fit

2 Header-Data Units in this file.
 
=================== HDU 1: Primary Array ===================
 
 29 header keywords
 
 Null data array; NAXIS = 0 
 
=================== HDU 2: BINARY Table ====================
 
 52 header keywords
 
 RATE  \(3 columns x 5371 rows\)
 
 Col# Name \(Units\)       Format
   1 TIME \(d\)             D         
   2 RATE \(counts\/s\)      E         
   3 ERROR \(counts\/s\)     E         
 
\+* Error Summary  \+*
 
 HDU#  Name \(version\)       Type             Warnings  Errors
 1                          Primary Array    0         0     
 2     RATE                 Binary Table     0         0     
 
\** Verification found 0 warning\(s\) and 0 error\(s\)\. \**
"""


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
        #print('entering setUp()')
        self.test_filename = 'my_rate.fit'
        self.test_filepath = os.path.join(PACKAGE_DIR, 'heasoftpy', 'tests', self.test_filename)
        self.maxDiff = 1000


    ftv_out = """ 
               ftverify 4.20 (CFITSIO V3.480)               
               ------------------------------               
 
HEASARC conventions are being checked.
 
File: my_rate.fit

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

        #    @unittest.skip('skipping fhelp')
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

    @unittest.skip('Skipping ftverify')
    def test_ftverify(self):
        """ Tests the ftverify program """
        test_result = heasoftpy.ftverify(infile=self.test_filepath, 
                                         numerrs=0, numwrns=0,
                                         stderr=True)
        test_out = test_result.stdout
        print('type(test_out): {}'.format(type(test_out)))
        test_err = test_result.stderr
        if isinstance(test_out, bytes):
            test_out = test_out.decode()
        if isinstance(test_err, bytes):
            test_out = test_err.decode()
#        self.assertEqual(test_out, expected_out)
        print(re.match(FTVERIFY_EXP_OUT, test_out))
        self.assertRegex(test_out, FTVERIFY_EXP_OUT)

    #@unittest.skip('Skipping ftverify_single_arg')
    def test_ftverify_single_arg(self):
        """ Tests the ftverify program using only one (positional) argument"""
        test_result = heasoftpy.ftverify(self.test_filepath)
        test_out = test_result.stdout
        with open('ftverify_single.out', 'wt') as mfile:
            mfile.write(test_out)
        test_err = test_result.stderr
        if isinstance(test_out, bytes):
            test_out = test_out.decode()
        if isinstance(test_err, bytes):
            test_out = test_err.decode()
#        self.assertEqual(test_out, expected_out)
        self.assertRegex(test_out, FTVERIFY_EXP_OUT)

if __name__ == '__main__':
    unittest.main()
