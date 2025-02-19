# Version tracking


## 0.2 (12/17/2021):
- Converted the functionality from the old code. Went through all the issues (up to #35) and issues and made sure all work in the new code, plus additional features.

## 0.2 (03/01/2022):
- Added testing and installation tools, fixed bugs from ixpe integration. Completed IXPE integration.

## 1.1 (04/13/2022)
- added remote caldb support to ixpechrgcorr.
  
## 1.2 (11/15/2022)
- Several bug fixes handling special cases in reading parameter files.
- Moved ixpe to main heaosft build, the final installation remains under heasoftpy.

## 1.2.1 (12/05/2022)
- Always use `$HEADAS/syspfiles` during installation
- Updated `utils.local_pfiles` to exclude `~/pfiles`
- fix for the case of parameter expecting a str and float is given

## 1.3 (07/12/2023)
- Fixed an issue of reading par files with extra white space
- Added timestamp check to read par files from sys_pfiles after a fresh installation
- Added a fix for cfitsio version conflict between astropy (through ixpe) and pyxspec
- Updated `utils.local_pfiles` to use tempfile instead of process id.
- Add `utils.local_pfiles_context` to be used as context manager for local pfiles
- Fix logging errors in ixpe tests.
- Moved mode check from `HSPTask` to `HSPTask.read_pfile` + code style updates. 
- Added HSPParams tests
- Added explicit ISO-8859-15 in the return of `subprocess.Popen`

## 1.4 (02/21/2024)
- Several maintenance updates:
    - Switch to automatic dev versioning using git SHA with setuptools-scm. 
    - Switch installation to use pyproject.toml instead of setup.py.
    - Added local-build.py to handle local building of the package.
    - Update installation instructions in README.
    - (1.4dev2) Restore the old numbered versioning.
    - (1.4dev3) Switch from fcn.* to individual components. Using fcn.* will give a warning.
    - (1.4dev4) Add _ixpe.py temporarily to handle deprecate messages.
    - (1.4dev5) Add subpackages with separate imports instead all tasks being under one single large packages. The subpackage groups are obtained from the pfiles_list.txt.

## 1.4.1 (03/21/2024)
- (1.5dev1) Fix a bug in reading files names with complex selection
- (1.5dev2) Fix the imports in heasoftpy.nicer.*
- (1.4.1dev3) Speed-up installation and change version to minor in preparation for patch release.

## 1.5 (TDB)
- (1.5dev0) Add BSD license after formal approval from UMD.
- (1.5dev1) Update pfiles_list.txt file to match that released with 6.34 (includes xrism software)
- (1.5dev2) Further Update pfiles_list.txt (mxpipeline.par).
- (1.5dev3): Improve code style
- (1.5dev4): Fix the bug of extra space in parameter names (e.g. xapipeline)
- (1.5dev5): change the install to use get_source_files instead of editing SOURCES.txt directly