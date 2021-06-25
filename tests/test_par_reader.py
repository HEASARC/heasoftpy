#!/usr/bin/env python

""" Tests of heasoftpy.par_reader """

import os
import re
import sys
import unittest

import heasoftpy.par_reader as par_reader

# try:
#     import heasoftpy.par_reader
# except ModuleNotFoundError:
    # A kludge to get the import to work, assuming the heasoftpy directory is
    # one level above the test directory.
    # CUR_FILE_DIR = os.path.dirname(os.path.abspath(__file__))
    # DIR_PARTS = CUR_FILE_DIR.split(os.sep)
    # PACKAGE_DIR = os.sep.join(DIR_PARTS[:-2])
    # sys.path.append(PACKAGE_DIR)
    #import heasoftpy.par_reader
#    from ..par_reader import *


class TestParReader(unittest.TestCase):
    """
    Class for testing heasoftpy's par_reader functions.
    """

    def setUp(self):
        """ Currently a placeholder """

    # Reference for following function:
    #    https://stackoverflow.com/questions/8389639/unittest-setup-teardown-for-several-tests
    @classmethod
    def setUpClass(cls):
        """ Currently a placeholder """

    def tearDown(self):
        """ Currently a placeholder """

    #@unittest.skip('Skipping test_type_switch_b')
    def test_type_switch_b(self):
        test_result = par_reader.type_switch('b')
        self.assertEqual(test_result, bool)

    #@unittest.skip('Skipping test_type_switch_f')
    def test_type_switch_f(self):
        # 'f' is for file, not float
        test_result = par_reader.type_switch('f')
        self.assertEqual(test_result, str)

    #@unittest.skip('Skipping test_type_switch_i')
    def test_type_switch_i(self):
        test_result = par_reader.type_switch('i')
        self.assertEqual(test_result, int)

    #@unittest.skip('Skipping test_type_switch_r')
    def test_type_switch_r(self):
        test_result = par_reader.type_switch('r')
        self.assertEqual(test_result, float)

    #@unittest.skip('Skipping test_type_switch_s')
    def test_type_switch_s(self):
        test_result = par_reader.type_switch('s')
        self.assertEqual(test_result, str)

    #@unittest.skip('Skipping test_typify_bool')
    def test_typify_bool(self):
        test_result = par_reader.typify('True', 'b')
        self.assertEqual(test_result, True)

    #@unittest.skip('Skipping test_typify_int')
    def test_typify_int(self):
        test_result = par_reader.typify('42', 'i')
        self.assertEqual(test_result, 42)

    #@unittest.skip('Skipping test_typify_real')
    def test_typify_real(self):
        test_result = par_reader.typify('0.42', 'r')
        self.assertEqual(test_result, 0.42)

    #@unittest.skip('Skipping test_typify_str')
    def test_typify_str(self):
        test_result = par_reader.typify('forty-two', 's')
        self.assertEqual(test_result, 'forty-two')

if __name__ == '__main__':
    unittest.main()
