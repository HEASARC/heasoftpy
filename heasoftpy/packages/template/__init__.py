__description__ = """
This is a template package for a python-only tasks.

The structure of the package for a single task should be:
packages/template/
            |-- __init__.py
            |-- setup.py
            |-- template.py
            |-- template_lib.py
            |-- template.par
            |-- template.html


For multiple tasks that are related to a mission for example, the 
recommended structure is:
packages/mission/
            |-- __init__.py
            |-- setup.py
            |-- template1
                |-- template1.py
                |-- template1_lib.py
                |-- template1.par
                |-- template1.html
            |-- template2
                |-- template2.py
                |-- template2_lib.py
                |-- template2.par
                |-- template2.html

Where:
-----
(replace "template" or "Template" with the name of your tool)

- __init__.py: should import the relevant modules to be exposed
    to the user, and include them in __all__.
    
- setup.py: This will be used during the installation, and should define a variable
    called `tasks` that contains a list of tasks provided by the package.
    If the above file structure is used, `tasks` should be a simple list of strings.
    So in the above 'complex' example. It is: 
    tasks = ['template1', 'template2']
    If the package structure is different, then the entry in the list is a dictionary of the form:
    [{taskname: [location_of_executable, location_of_parameter_file, location_of_help_file]}]. 

    Additionally, if the package uses external packages that are not
    dependencies of heasoftpy, a variable called `requirements` must also
    be defined in setup.py, which defines a list of these dependencies.
    The list of dependecies can also be specified in a requirements.txt file.
    
    See the example in template/setup.py.

- template.par: This is a standard parameter file that will be used
    to integrate the task into HEASoft.

- template_lib.py: This is the main module that acts as a wrapper for your 
    code to integrate it within heasoftpy.
    It should define:
        ++ a class `TemplateTask` that inherits from `HSPTask`, and defines 
            a method called `exec_task`, that runs the task code, and returns an 
            HSPResult object. The class should also define the `name` attribute.
            
        ++ a method `template` that creates an instance of `TemplateTask` and 
            calls to run the task. This will be accessible to the user though: 
            `heasoftpy.template`.
    
    This file can contain other methods that are needed to run the task,
    or it could contain calls to other modules or sub-packages.
    For the task to integrate with heasoftpy, feedback text should be 
    communicated through the provided logger, which uses the standard python
    logging library. Inside TemplateTask, the logger can be accessed with
    `logger = self.logger`, while outside TemplateTask, it can be invoked
    with logging.getLogger(template). Once loaded, simple informational messages 
    can be written as: `logger.info(message)` and errors as `logger.error(message)`.
    
    The task parameters are available inside TemplateTask in a dictionary called `params`.
    If you wish the task to update these parameters and write them to the user's .par file
    after execution (typically not needed), you can update the params dict like: 
    `self.params['some_parameter'] = new_value`.
    Then, inside `exec_task`, just before returning an HSPResult object, run the following
    to write to the parameter file:
    ```
    usr_pfile = HSPTask.find_pfile(self.name, return_user=True)
    self.write_pfile(usr_pfile)
    ```
    
- template.py: This is a short executable script. This will be moved $HEADAS/bin 
    during installation, and become available to the user.
    The requirement here is that the same class (e.g. `TemplateTask`) 
    defined in `template_lib.py` is used, along with the matching task name.
    
- template.py.html: The help file that prints the help for the task. This format
    is recommended, so it can be read by fhelp, which the standard way for printing
    the help of tasks. The user can invoke the help for the template task by doing
    `fhelp template.py`
    
- requirements.txt: a list of required packages, one per line, that the package needs.
    The requirements can also specified as a list of strings in variable called 
    `requirements` in setup.py. If this variable is given, and it is not an empty list,
    the requirements.txt file will be ignored.

"""


from .template_lib import TemplateTask, template
__all__ = ['TemplateTask', 'template']