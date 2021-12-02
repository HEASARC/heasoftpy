
__description__ = """
contrib is the package where all python-only tasks reside. 
Each should written as a separate package in its own folder.

The template package included gives an example of how such packages
are to be written:
- The package should be placed inside the current directory (contrib).
- A line importing the content of the package should be added here. 
    (e.g: `from .template import *`)
    
The first three lines import the core modules of heasoftpy, so they
can be used within the packages

"""


# import the sub-packages.
from .template import *