
"""
Define a data structure for holding results from FTools runs via the
heasoftpy interface.
"""

# The nametuple approach did not work once it became necessary to change
# the values after a Result was instantiated.
#
#import collections
# Result is a namedtuple to hold results of the FTools runs by subprocess.
# The methods for setting the fields and default values are are borrowed from:
#   https://stackoverflow.com/a/18348004/197011
#result_fields =  ('returncode', 'stdout', 'stderr', 'params', 'custom')
#Result = collections.namedtuple('Result', result_fields)
#Result.__new__.__defaults__ = (None, None, None)


class Result:
    def __init__(self, ret_code, std_out, std_err=None, parms=None, custm=None):
        self.returncode = ret_code
        self.stdout = std_out
        self.stderr = std_err
        self.params = parms
        self.custom = custm
