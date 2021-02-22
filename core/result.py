
"""
Define a data structure for holding results from FTools runs via the
heasoftpy interface.
"""

# The namedtuple approach did not work once it became necessary to change
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
    """ Container for data returned from heasoftpy call to a HEAsoft tool """
    def __init__(self, ret_code, std_out, std_err=None, parms=None, custm=None):
        self.returncode = ret_code
        self.stdout = std_out
        self.stderr = std_err
        self.params = parms
        self.custom = custm
        self.output = std_out.split('\n')

    def __str__(self):
        if self.returncode is None:
            ret_code_str = 'returncode: None'
        else:
            ret_code_str = ' '.join(['returncode:', str(self.returncode)])
        if self.stderr:
            stdout_str = '\n'.join(['stdout:', self.stdout])
            stderr_str = '\n'.join(['stderr:', self.stderr])
        else:
            stdout_str = '\n'.join(['stdout (including stderr):', self.stdout])
            stderr_str = 'stderr: None - included in stdout'
        param_str = 'params:\n'
        if self.params:
            for par_key in self.params.keys():
                param_str += '  ' + par_key + ': ' + self.params[par_key] + '\n'
        else:
            param_str += '  None'
        if self.custom:
            custom_str = ' '.join(['custom:', str(self.custom)])
        else:
            custom_str = 'custom: None'
        res_str = '\n'.join([ret_code_str, stdout_str, stderr_str,
                             param_str, custom_str])
        return res_str
