

import sys

from ...core import HSPTask, HSPResult, HSPLogger
from ... import fcn, utils


class TemplateTask(HSPTask):
    """Sample python-based task"""
    
    
    def exec_task(self):
        
        # put the parameters in to a list of par=value
        params = self.params
        
        # logger
        logger = self.logger
        
        # return code: 0 if task runs sucessful; set to 0 at the end
        returncode = 1
        
        
        ## ----------------- ##
        ##  start code here  ##
        ## ----------------- ##
        msg = f"""\nResetting the foo parameter from {params['foo']} to {params['bar']}.\n"""        
        logger.message(msg)
        
        params['foo'] = f"{params['bar']}" #  stringify the int
        msg = f"Now foo = {params['foo']}."
        logger.message(msg)
        
        params['bar'] = _some_addition_function(params['bar'])
        msg = f" and bar = {params['bar']}.\n"
        logger.message(msg)
        
        logger.error('No error, but checking\n')
        returncode = 0
        ## ----------------- ##
        ##  end code  ##
        ## ----------------- ##

        outMsg, errMsg = logger.getValue()
        return HSPResult(returncode, outMsg, errMsg, params)
    
    def task_docs(self):
        """Leave like this to use the docstring in the task method below 
        This is the help text to be printed when passing -h to the command 
        line executable of the task
        """
        return template.__doc__


def _some_addition_function(inval):
    return inval+1


def template(args=None, **kwargs):
    """
    Write your task help text here.
    
    """
    template_task = TemplateTask('template')
    result = template_task(args, **kwargs)
    return result

