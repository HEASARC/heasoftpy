#! /usr/bin/env python
"""
A library of functions for this mission template.  It may
include lower level functions and or a single function for 
each executable.  
"""

from heasoftpy.core import result as hsp_res
from heasoftpy.ape import Params


def tjtest1(inpars=None,**kwargs):
    """Sets foo to bar"""
    if inpars and type(inpars) is Params:
        pars = inpars.to_simple_dict()
    else:
        pars = Params(inpars,name="tjtest1",**kwargs).to_simple_dict()

    ## ----------
    ##  Your code here
    out = f"""Resetting the foo parameter from {pars['foo']} to {pars['bar']}.\n"""
    pars['foo'] = f"{pars['bar']}" #  stringify the int
    out += f"Now foo = {pars['foo']}."
    pars['bar'] = utilfunc(pars['bar'])
    out += f" and bar = {pars['bar']}."
    ## ----------

    return hsp_res.Result(0,out,None,pars)


def utilfunc(inval):
    return inval+1


