import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import heasoftpy as hsp

class SampleTask(hsp.HSPTask):
    """Sample python-based task"""
    
    
    def exec_task(self):
        
        # put the parameters in to a list of par=value
        all_params = self.all_params
        usr_params = self.params
        
        ## ----------
        ##  Your code here
        out = f"""Resetting the foo parameter from {usr_params['foo']} to {usr_params['bar']}.\n"""
        usr_params['foo'] = f"{usr_params['bar']}" #  stringify the int
        out += f"Now foo = {usr_params['foo']}."
        usr_params['bar'] = utilfunc(usr_params['bar'])
        out += f" and bar = {usr_params['bar']}."
        ## ----------

        return hsp.HSPResult(0, out, None, usr_params)
    
    def task_docs(self):
        docs = "*** Documentation for the sample code goes here! ***"
        return docs

def utilfunc(inval):
    return inval+1

if __name__ == '__main__':
    # test the code here
    os.environ['PFILES'] = os.getcwd() + '/contrib;' + os.environ['PFILES']
    
    sample = SampleTask(name='sample')
    cmd_args = hsp.utils.process_cmdLine(sample)
    sample(**cmd_args)