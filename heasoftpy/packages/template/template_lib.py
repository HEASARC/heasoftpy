

import sys
import logging

from heasoftpy.core import HSPTask, HSPResult
from heasoftpy import fcn, utils


class TemplateTask(HSPTask):
    """Sample python-based task"""
    
    
    def exec_task(self):
        
        # put the parameters in to a list of par=value
        params = self.params
        
        # logger
        logger = logging.getLogger(self.name)
        # or logger = self.logger
        # or logger = logging.getLogger('template')
        
        # return code: 0 if task runs sucessful; set to 0 at the end
        returncode = 1
        
        
        ## ----------------- ##
        ##  start code here  ##
        ## ----------------- ##
        logger.info(f"Resetting the foo parameter from {params['foo']} to {params['bar']}.")
        
        params['foo'] = f"{params['bar']}" #  stringify the int
        logger.info(f"Now foo = {params['foo']}.")
        
        params['bar'] = _some_additional_function(params['bar'])
        logger.info(f"and bar = {params['bar']}.")
        
        logger.error('testing error logging')
        returncode = 0
        ## ----------------- ##
        ##  end code  ##
        ## ----------------- ##

        outMsg, errMsg = self.logger.output
        return HSPResult(returncode, outMsg, errMsg, params)
    
    
    def task_docs(self):
        """Leave like this to use the docstring in the task method below 
        This is the help text to be printed when passing -h to the command 
        line executable of the task
        """
        return template.__doc__


def _some_additional_function(inval):
    return inval+1


def template(args=None, **kwargs):
    """
    Write your task help text here.
    
    """
    template_task = TemplateTask('template')
    result = template_task(args, **kwargs)
    return result

