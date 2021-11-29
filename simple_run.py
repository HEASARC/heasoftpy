
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))


import heasoftpy


# class HSPParam():
    
#     def __init__(self, line):
#         self.name = line[0]
#         self.value = line[1]

    
#     def __set__(self, obj, new_value):
#         if obj is None:
#             return self
#         self.value = new_value
        
#     def __repr__(self):
#         return f'{self.value}'

# class Dum():
    
#     def __init__(self):
#         self.i1 = HSPParam(['name1', 33])
#         self.i2 = HSPParam(['name2', 44])
    
        
#     def __getattribute__(self, name):
#         attrObj = super(Dum, self).__getattribute__(name)
#         if hasattr(attrObj, '__get__'):
#             return attrObj.__get__(self, Dum)
#         return attrObj
    
#     def __setattr__(self, attr, val):
#         try:
#             attrObj = super(Dum, self).__getattribute__(attr)
#         except AttributeError:
#             # setting for the first time
#             super(Dum, self).__setattr__(attr, val)
#         else:
#             if hasattr(attrObj, '__set__'):
#                 attrObj.__set__(self, val)
#             else:
#                 super(Dum, self).__setattr__(attr, val)



if __name__ == '__main__':

    ftlist = heasoftpy.HSPTask('ftlist')
    ftlist.infile = 'tests/test.fits'
    ftlist(option='T', verbose=True)
