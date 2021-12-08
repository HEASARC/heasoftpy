__description__ = """
This is a template package for a python-only tasks.

The package should include the following:

- template.par: This is a standard parameter file that will be used
    to integrate the task into HEASoft.

- __init__.py: to indicate what modules, and methods are to be exposed
    to the user.

- template_lib.py (or taskname_lib.py): This is the main module that acts
    as a wrapper for your code to integrate it within heasoftpy.
    It should define:
        ++ a class `TemplateTask` (or `TasknameTaks`) that inherits 
           from `HSPTask`, and define a method called `exec_task`, that 
           runs the task code, and returns an HSPResult object.
        ++ a method `template` (or `taskname`) that creates an instance
            of `TemplateTask` and calls to run the task. This will be 
            accessible to the user though: `heasoftpy.packages.template`
    This file can contain other methods that are needed to run the task,
    or it could contain calls to other modules or sub-packages created
    under the `template` package.
    For the task to integrate with heasoftpy, feedback text should be 
    
    communicated with the provided logger, which uses the standard python
    logging library. Inside TemplateTask, the logger can be accessed with
    `logger = self.logger`, while outside TemplateTask, it can be invoked
    from the logging with logging.getLogger(taskname) (taskname=template here).
    Once loaded, simple informational messages can be written as: 
    `logger.info(message)` amd errors as `logger.error(message)`.
    
    
- template.py (or generally taskname.py): This is a short 
    executable script that has the `__name__ == '__main__'`. This will 
    be moved $HEADAS/bin during the installation, and become available 
    to the user.
    The requirement here is that the same class (e.g. `TemplateTask`) 
    defined in `template.py` is used, along with the matching task name.

- below import all classes and methods that you wish to be availabe to the
user in heasoftpy.packages.*; Classes and methods that are only relevent to 
this task should not be directly exposed, and should remain accessible only
though this task module: e.g. heasoftpy.packages.template_lib.*.

"""


from .template_lib import TemplateTask, template

__all__ = ['TemplateTask', 'template']