# version tracking
# ----------------
# number   | MM/DD/YYYY  | Description (Author: comments)
# ------   | ----------  | ------------------------------
# 0.2      | 12/17/2021  | AZ: converted the functionality from the old code. Went
#          |             | throguh all the issues (up to #35) and issues and made
#          |             | made sure all work in the new code, plus additional features.
#--------------------------------------------------------
# 1.0      | 03/01/2022  | AZ: added testing and installation tools, fixed bugs from
#          |             | ixpe integration. Completed IXPE integration.
#--------------------------------------------------------
# 1.1      | 04/13/2022  | AZ: - added remote caldb support to ixpechrgcorr.
#--------------------------------------------------------
# 1.2      | 11/15/2022  | - Several bug fixes handling special cases in reading parameter files.
#          |             | - Moved ixpe to main heaosft build, the final installation remains
#          |             | under heasoftpy.
#--------------------------------------------------------
# 1.3dev   | TBD         | - Always use $HEADAS/syspfiles during installation
#          |             | - updated utils.local_pfiles to exclude ~/pfiles
#          |             | - fix for the case of parameter expecting a str and float is given
#

__version__ = '1.3dev'
