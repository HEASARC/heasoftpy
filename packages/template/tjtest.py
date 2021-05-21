#! /usr/bin/env python
"""
A library of functions for this mission template.  It may
include lower level functions and or a single function for 
each executable.  
"""

from heasoftpy.core import result as hsp_res
from heasoftpy.ape import params


def tjtest1(inpars=None,**kwargs):
    """Sets foo to bar"""
    #  Need to reset stdout and stderr to pass back in Result
    if inpars and type(inpars) is params:
        pars=params(inpars,name="tjtest1")
    else:
        pars = params(**kwargs,name="tjtest1")

    ## ----------
    ##  Your code here
    out=f"""Resetting the foo parameter from {pars['foo']} to {pars['bar']}.\n"""
    pars['foo']=f"{pars['bar']}" #  stringify the int
    out+="Now foo = {}.".format(pars['foo'])
    pars['bar']=utilfunc(pars['bar'])
    out+=" and bar = {}.".format(pars['bar'])
    ## ----------

    return hsp_res.Result(0,out,None,pars)


def utilfunc(inval):
    return inval+1


