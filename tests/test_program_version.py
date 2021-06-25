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
    import heasoftpy.program_version
except ModuleNotFoundError:
    # A kludge to get the import to work, assuming the heasoftpy directory is
    # one level above the test directory.
    sys.path.append(PACKAGE_DIR)
    import heasoftpy.program_version


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
        """ Currently a placeholder """

    def tearDown(self):
        """ Currently a placeholder """

    #@unittest.skip('Skipping test_read_version')
    def test_read_version(self):
        """ Tests the read_version function """
        ver_format = re.compile(r'\d*\.\d*\.\d*')
        test_result = heasoftpy.program_version.read_version(os.path.join(PACKAGE_DIR, 'heasoftpy'))
        self.assertRegex(test_result, ver_format)

    #@unittest.skip('Skipping test_version_compare')
    def test_version_compare(self):
        lesser_ver = heasoftpy.program_version.ProgramVersion('0.0.1')
        greater_ver = heasoftpy.program_version.ProgramVersion('1.0.0')
        self.assertGreater(greater_ver, lesser_ver)
        
if __name__ == '__main__':
    unittest.main()
