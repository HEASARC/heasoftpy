#!/usr/bin/env python

""" Tests of heasoftpy.utils """

import os
import re
import sys
import unittest

CUR_FILE_DIR = os.path.dirname(os.path.abspath(__file__))
DIR_PARTS = CUR_FILE_DIR.split(os.sep)
PACKAGE_DIR = os.sep.join(DIR_PARTS[:-2])

try:
    import heasoftpy.utils
except ModuleNotFoundError:
    # A kludge to get the import to work, assuming the heasoftpy directory is
    # one level above the test directory.
    sys.path.append(PACKAGE_DIR)
    import heasoftpy.utils


class TestUtils(unittest.TestCase):
    """
    Class for testing heasoftpy utils functions.
    """

    def setUp(self):
        """ Currently a placeholder """

    # Reference for following function:
    #    https://stackoverflow.com/questions/8389639/unittest-setup-teardown-for-several-tests
    @classmethod
    def setUpClass(cls):
        """ Sets up test parameters, etc. These tests may contain invalid values. """
        cls.test_key1 = 'test_key1'
        cls.test_key2 = 'test_key2'
        cls.test_param_dict = {'test_key1': {'mode': 'q', 'type': 's'},
                               'test_key2': {'mode': 'z', 'type': 'r'}}
#        print('test_key1: {}\ntest_key2: {}\ntest_param_dict: {}'.format(cls.test_key1, cls.test_key2, cls.test_param_dict))

    def tearDown(self):
        """ Currently a placeholder """

    #@unittest.skip('Skipping test_check_query_param_found')
    def test_check_query_param_found(self):
        self.assertTrue(heasoftpy.utils.check_query_param(self.test_key1, self.test_param_dict))

    #@unittest.skip('Skipping test_check_query_param_notfound')
    def test_check_query_param_notfound(self):
        self.assertFalse(heasoftpy.utils.check_query_param(self.test_key2, self.test_param_dict))

    #@unittest.skip('Skipping test_is_param_ok')
    def test_is_param_ok(self):
        self.assertTrue(heasoftpy.utils.is_param_ok((self.test_key2, '1.0'), self.test_param_dict))

    #@unittest.skip('Skipping test_read_version')
    def test_read_version(self):
        """ Tests the read_version function """
        ver_format = re.compile(r'\d*\.\d*\.\d*')
        test_result = heasoftpy.utils.read_version(os.path.join(PACKAGE_DIR, 'heasoftpy'))
        self.assertRegex(test_result, ver_format)

    #@unittest.skip('Skipping test_type_switch_b')
    def test_type_switch_b(self):
        test_result = heasoftpy.utils.type_switch('b')
        self.assertEqual(test_result, bool)

    #@unittest.skip('Skipping test_type_switch_f')
    def test_type_switch_f(self):
        # 'f' is for file, not float
        test_result = heasoftpy.utils.type_switch('f')
        self.assertEqual(test_result, str)

    #@unittest.skip('Skipping test_type_switch_i')
    def test_type_switch_i(self):
        test_result = heasoftpy.utils.type_switch('i')
        self.assertEqual(test_result, int)

    #@unittest.skip('Skipping test_type_switch_r')
    def test_type_switch_r(self):
        test_result = heasoftpy.utils.type_switch('r')
        self.assertEqual(test_result, float)

    #@unittest.skip('Skipping test_type_switch_s')
    def test_type_switch_s(self):
        test_result = heasoftpy.utils.type_switch('s')
        self.assertEqual(test_result, str)

    #@unittest.skip('Skipping test_typify_bool')
    def test_typify_bool(self):
        test_result = heasoftpy.utils.typify('True', 'b')
        self.assertEqual(test_result, True)

    #@unittest.skip('Skipping test_typify_int')
    def test_typify_int(self):
        test_result = heasoftpy.utils.typify('42', 'i')
        self.assertEqual(test_result, 42)

    #@unittest.skip('Skipping test_typify_real')
    def test_typify_real(self):
        test_result = heasoftpy.utils.typify('0.42', 'r')
        self.assertEqual(test_result, 0.42)

    #@unittest.skip('Skipping test_typify_str')
    def test_typify_str(self):
        test_result = heasoftpy.utils.typify('forty-two', 's')
        self.assertEqual(test_result, 'forty-two')

    #@unittest.skip('Skipping test_version_compare')
    def test_version_compare(self):
        lesser_ver = heasoftpy.utils.ProgramVersion('0.0.1')
        greater_ver = heasoftpy.utils.ProgramVersion('1.0.0')
        self.assertGreater(greater_ver, lesser_ver)
        
if __name__ == '__main__':
    unittest.main()
