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

    def tearDown(self):
        """ Currently a placeholder """

    #@unittest.skip('Skipping test_read_version')
    def test_read_version(self):
        """ Tests the read_version function """
        ver_format = re.compile(r'\d*\.\d*\.\d*')
        test_result = heasoftpy.utils.read_version(os.path.join(PACKAGE_DIR, 'heasoftpy'))
        self.assertRegex(test_result, ver_format)

if __name__ == '__main__':
    unittest.main()
