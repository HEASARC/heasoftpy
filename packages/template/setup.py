import sys, os, shutil
#  This needs to be an automated install of some sort
syspfiles=os.environ['PFILES'].split(';')[-1]
shutil.copyfile("./tjtest1.par",f"{syspfiles}/tjtest1.par")
shutil.copyfile("./tjtest1.py","../../defs/tjtest1.py")

##  No, this doesn't make sense.  heasoftpy has its own
##   module import infrastructure
#shutil.copyfile("./tjtest.py","../../lib/tjtest.py")
##
##  So insert something that will import tjtest as a sub-package of heasoftpy
##  with its modules tjtest1 etc.  
 
