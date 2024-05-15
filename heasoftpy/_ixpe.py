# Copyright 2024, University of Maryland, All Rights Reserved
# A temporary file to add deprecation
# warning to ixpe tasks when used from the
# top level heasoftpy. 
# `import heasoftpy` will not import ixpe by default 

import os
from functools import wraps
from astropy.utils.decorators import deprecated
from .core import HSPDeprecationWarning
from . import ixpe

__all__ = ['ixpechrgcorr', 'ixpeaspcorr', 'ixpecalcfov', 'ixpedet2j2000', 'ixpeexpmap',
           'ixpepolarization', 'ixpeboomdriftcorr']

def _wrap_task(task):
    name = task.__name__
    @wraps(task)
    @deprecated(
    since="1.4",
    message=(f"heasoftpy.{name} is being deprecated and will be removed. "
             f"Use ``heasoftpy.ixpe.{name}`` instead"),
    alternative=f"Use ``heasoftpy.ixpe.{name}`` instead",
    warning_type=HSPDeprecationWarning)
    def wrapper(args=None, **kwargs):
        ixpe_task = getattr(ixpe, name)
        return ixpe_task(args, **kwargs)
    return wrapper

ixpeaspcorr = _wrap_task(ixpe.ixpeaspcorr)
ixpechrgcorr = _wrap_task(ixpe.ixpechrgcorr)
ixpecalcfov = _wrap_task(ixpe.ixpecalcfov)
ixpedet2j2000 = _wrap_task(ixpe.ixpedet2j2000)
ixpeexpmap = _wrap_task(ixpe.ixpeexpmap)
ixpepolarization = _wrap_task(ixpe.ixpepolarization)
ixpeboomdriftcorr = _wrap_task(ixpe.ixpeboomdriftcorr)
