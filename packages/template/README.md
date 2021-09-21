
#  Template for a Python-native HEASoft package.

This is a template sub-package that may contain a number of routines that can be used
as an executable or as a library module.

##  To make your own package:

- Copy the template subdir to, e.g., a directory named ixpe.

- Replace the tjtest.py with your code as a library of modules.  You
  can have more than one obviously.  Your modules just need to take a
  single argument or dictionary of kwargs and to include the top block
  of code from the example.  The params class will do the rest.  

- Add the routines you want visible in the heasoftpy.ixpe package to
  the __init__.py file following the example.  

- Create an executable for each of your routines following the
  tjtest1.py example.  You should need to change nothing but
  "tjtest1"->"ixpe_doit" , or whatever you call it.  This is a work in
  progress, but it should not get much more complicated than this.
  Again, all the brains are in your library module and our params class.  

- Create a parameter file following the usual FTOOLS format, as in the example tjtest1.par.

- We will need some sort of install script to simply copy the files
  into central bin and syspfiles locations.  TBD.  For now it
  just has a couple of copy commands.  

- There's a script called testit that calls the tjtest1 function in a
  number of different ways so you can see what the options are that
  the params class should handle automagically.  



##  Known issues

When you use the top level install.py, you see warnings where it's trying to convert default
values into the correct Python type.  This is not important for the wrappers to compiled
executables, so you can ignore those.  But it will also warn you if you have an incorrect
type default in your parameter file.  So don't use a string like 'INDEF' for an integer type parameter,
as you can in other FTOOLS.



