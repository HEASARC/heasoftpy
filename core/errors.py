"""
Custom Error classes for heasoftpy.
"""

#import heasoftpy.result

class HeasoftpyError(Exception):
    """ Base Error Class for the module """
    pass

class HeasoftpyExecutionError(HeasoftpyError):
    """
    Error class for when one of the generated functions encounters an error
    running the program it wraps.
    """
    def __init__(self, prog, rslt):
        self.program = prog
        self.result = rslt

    def __str__(self):
        prog_output = ''
        if self.result.stderr:
            prog_output = '\n'.join(['stdout:', self.result.stdout, 'stderr:', self.result.stderr])
        else:
            prog_output = '\n'.join(['output:', self.result.stdout])
        obj_str = ''.join(['\nError running: ', self.program, '\nreturncode: ',
                           str(self.result.returncode), '\n', prog_output])
        return obj_str
