
import os as _os
import glob as _glob
_modules = _glob.glob(_os.path.join(_os.path.dirname(__file__), '*.py'))
_modules = [_os.path.basename(f)[:-3] for f in _modules if _os.path.isfile(f) 
           and not f.endswith('__init__.py')]

for _m in _modules:
    exec(f'from .{_m} import {_m}')