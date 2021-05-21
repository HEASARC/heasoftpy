#! /usr/bin/env python
from heasoftpy.ape import params
from heasoftpy.packages.template import tjtest1 

if __name__ == "__main__":
    with params(name="tjtest1") as pars:  
        try:
            result=tjtest1(**dict(pars))
            print(result.stdout)
            ##  If you return info through the parameter file, 
            ##   then update the pars object with what came out
            # pars.update(result.params)
        except:
            raise
        exit
