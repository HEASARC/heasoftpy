#! /usr/bin/env python
from heasoftpy.packages.template import tjtest1
from heasoftpy import fdump
import unittest
from unittest.mock import patch

class TestPackageTemplate(unittest.TestCase):

    def setUup(self):
        pass

    def tearDown(self):
        pass

    def test_CommandLine(self):
        import subprocess
        result=subprocess.run("packages/template/tjtest1.py infile=tests/test_rate.fit foo=xyz bar=20", shell=True, check=True)  
        assert result.returncode == 0

###   TO BE FIXED
#    @patch('builtins.input',side_effect=["foo.fits","oof","3"])
#    def test_Query(self,mock_input):
#        try: 
#             result=tjtest1()
#        except Exception as e:
#             print(f"ERROR:  {e}")
#        assert 'Resetting' in result.stdout

    def test_Kwargs(self):
        try:
             result=tjtest1(foo='oof',bar=3,infile='foo.fits')
        except Exception as e:
             print(f"ERROR:  {e}")
        assert 'Resetting' in result.stdout

        result.params['foo']='test3'
        try:
             result=tjtest1(result.params)
        except Exception as e:
             print(f"ERROR:  {e}")
        assert 'Resetting' in result.stdout

    def test_Dict(self):
        try:
             result=tjtest1({"foo":"oof","bar":10,"infile":"foo.fits"})
             print(result.stdout)
        except Exception as e:
             print(f"ERROR:  {e}")
        assert 'Resetting' in result.stdout





class BrokenTests(unittest.TestCase): 

    print("\n-----------------------------")
    print("Test 5:  run fdump instead, with prhead='no';\n          BROKEN should query for all and then print header  Output:\n--------")
    try:
         result=fdump(prhead="no")
         print(result.stdout)
    except Exception as e:
         print(f"ERROR:  {e}")


    print("\n-----------------------------")
    print("Test 6:  fdump given infile and mode='h';\n          BROKEN should not query.  Output:\n--------")
    try:
         result=fdump(infile="../../tests/test_rate.fit",mode="h",prhead="no",rows="1-5")
         print(result.stdout)
    except Exception as e:
         print(f"ERROR:  {e}")

    print("\n-----------------------------")
    print("Test 7:  fdump with dictionary, mode=h;\n      BROKEN  Currently broken, you have to interrupt or hit return a few times.\n     It should not query for anything and should not prhead  Output:\n--------")
    try:
         result=fdump({'infile':"../../tests/test_rate.fit",'mode':"h",'prhead':"no"})
         print(result.stdout)
    except Exception as e:
         print(f"ERROR:  {e}")


    print("\n-----------------------------")
    print("Test 8:  fdump with Params object;\n        BROKEN  Currently broken, you have to interrupt or hit return a few times.\n       Should not prhead or query anything.   Output:\n--------")
    try:
         result.params['prhead']="no"
         result=fdump(result.params)
         print(result.stdout)
    except Exception as e:
         print(f"ERROR:  {e}")






if __name__ == '__main__':
    unittest.main()
