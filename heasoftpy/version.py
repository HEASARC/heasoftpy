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
# 1.2.1    | 12/05/2022  | - Always use $HEADAS/syspfiles during installation
#          |             | - updated utils.local_pfiles to exclude ~/pfiles
#          |             | - fix for the case of parameter expecting a str and float is given
#--------------------------------------------------------
# 1.3      | 07/12/2023  | AZ: 1- fixed an issue of reading par files with extra white space
#          |             | AZ: 2- added timestamp check to read par files from sys_pfiles after a fresh installation
#          |             | AZ: 3- added a fix for cfitsio version conflict between astropy (through ixpe) and pyxspec
#          |             | AZ: 4- updated utils.local_pfiles to use tempfile instead of process id.
#          |             | AZ: 5- add utils.local_pfiles_context to be used as context manager for local pfiles
#          |             | AZ: 6- Fix logging errors in ixpe tests.
#          |             | AZ: 7- Moved mode check from HSPTask to HSPTask.read_pfile + code style updates. 
#          |             |      - Added HSPParams tests
#          |             |      - Added explict ISO-8859-15 in the return of subprocess.Popen
#          |             |


__version__ = '1.3'
