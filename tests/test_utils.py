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

if __name__ == '__main__':
    unittest.main()
