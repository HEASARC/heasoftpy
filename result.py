
class Result:
    def __init__(self, ret_code, std_out, std_err=None, parms=None, custm=None):
        self.returncode = ret_code
        self.stdout = std_out
        self.stderr = std_err
        self.params = parms
        self.custom = custm









