import sys, os, shutil
#  This needs to be an automated install of some sort
syspfiles=os.environ['PFILES'].split(';')[-1]
shutil.copyfile("./tjtest1.par",f"{syspfiles}/tjtest1.par")
shutil.copyfile("./tjtest1.py",f"{os.environ['HEADAS']}/bin/")


