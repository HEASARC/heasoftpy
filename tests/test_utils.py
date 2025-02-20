
from .context import heasoftpy

import os
import sys
import unittest
from unittest.mock import patch


class TestUtils(unittest.TestCase):
    """Tests for heasoftpy.utils"""
    # setUp and tearDown ensures PFILES is restored to what it was
    def setUp(self):
        self.pfiles = os.environ['PFILES']

    def tearDown(self):
        os.environ['PFILES'] = self.pfiles

    # temp file; no input to local_pfiles
    def test__utils__local_pfiles_tmpfile(self):
        pDir = heasoftpy.utils.local_pfiles()
        self.assertEqual(pDir[-7:],  '.pfiles')
        self.assertTrue(pDir in os.environ['PFILES'])
        os.rmdir(pDir)
        os.environ['PFILES'] = self.pfiles

    # input is a file not a dir
    def test__utils__local_pfiles_file(self):
        tfile = os.path.join('/tmp', str(os.getpid()) + '.pfiles.tmp')
        with open(tfile, 'w') as fp:
            fp.write('')
        with self.assertRaises(OSError):
            heasoftpy.utils.local_pfiles(tfile)
        os.remove(tfile)

    # don't have permission
    def test__utils__local_pfiles_permission(self):
        with self.assertRaises(OSError):
            heasoftpy.utils.local_pfiles('/not-allowed')

    # user gives a dir
    def test__utils__local_pfiles_someDir(self):
        pDir = os.path.join('/tmp', str(os.getpid()) + '.tmp')
        oDir = heasoftpy.utils.local_pfiles(pDir)
        self.assertEqual(pDir, oDir)
        self.assertTrue(pDir in os.environ['PFILES'])
        os.rmdir(pDir)
        os.environ['PFILES'] = self.pfiles

    # ensure a task writes to the local pfile created by the user
    def test__utils__local_pfiles_someDir_ensure_write(self):
        pDir = os.path.join('/tmp', str(os.getpid()) + '.tmp')
        heasoftpy.utils.local_pfiles(pDir)
        heasoftpy.fhelp(task='ftlist')
        self.assertTrue(os.path.exists(f'{pDir}/fhelp.par'))
        os.remove(f'{pDir}/fhelp.par')
        os.rmdir(pDir)
        os.environ['PFILES'] = self.pfiles

    # test using local_pfiles_context
    def test__utils__local_pfiles_context(self):
        pDir = os.path.join('/tmp', str(os.getpid()) + '.tmp')

        with heasoftpy.utils.local_pfiles_context(pDir):
            self.assertTrue(pDir in os.environ['PFILES'])

        self.assertFalse(pDir in os.environ['PFILES'])

    def test_find_module_name__unknown(self):
        with self.assertRaises(ValueError):
            heasoftpy.utils.find_module_name('unknown')

    def test_find_module_name(self):
        self.assertTrue(
            'ftools' == heasoftpy.utils.find_module_name('fdump')
        )
        self.assertTrue(
            'heatools' == heasoftpy.utils.find_module_name('ftlist')
        )
        self.assertTrue(
            'attitude' == heasoftpy.utils.find_module_name('attconvert')
        )

    def test_find_module_name__w_hsp_nokey(self):
        with patch('heasoftpy._modules.mapper', {}):
            self.test_find_module_name()

    def test_find_module_name__w_hsp_importError(self):
        with patch.dict(sys.modules, {"heasoftpy._modules": None}):
            self.test_find_module_name()


# def test_pfiles_list():
#     """Ensure pfiles_list.txt is up to date.
#     Because the develop version may have more tasks than
#     the released version, we ensure that syspfiles/pfiles_list.txt
#     is at least a subset of the checked file.
#     The checked file should contain the all possible tasks, including
#     new ones, and possibly deleted ones too. For the deleted ones, they
#     can be removed once develop becomes a release.
#     """
#     our_f = 'pfiles_list.txt'
#     hea_f = f"{os.environ['HEADAS']}/syspfiles/pfiles_list.txt"
#     # do check only if hea_f is present
#     if not os.path.exists(hea_f):
#         return
#     our_m = {}
#     for line in open(our_f).readlines():
#         mod, task = line.strip().split(':')
#         if mod not in our_m:
#             our_m[mod] = []
#         our_m[mod].append(task)
#     hea_m = {}
#     for line in open(hea_f).readlines():
#         mod, task = line.strip().split(':')
#         if mod not in hea_m:
#             hea_m[mod] = []
#         hea_m[mod].append(task)
#     for k in hea_m.keys():
#         assert k in our_m
#         for task in hea_m[k]:
#             assert task in our_m[k]
