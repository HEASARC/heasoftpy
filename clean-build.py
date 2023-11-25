import os
import glob
    
def _do_clean():
    """Removes the wrappers in heasoftpy/fcn and temporary files"""
    fcn = os.path.join('heasoftpy', 'fcn')
    print(f'cleaning wrappers in {fcn}')
    filelist = [f for f in os.listdir(fcn) if '.py' == f[-3:] and not '__' in f]
    for f in filelist:
        file = os.path.join(fcn, f)
        print(f'removing {file}')
        os.remove(file)
    cwd = os.getcwd()
    for d in ['build', 'heasoftpy.egg-info', '__pycache__', 'dist', 
              'heasoftpy-install.log', f'{fcn}/__pycache__', '.pytest_cache',
             '.eggs', '*.pyc', '.ipynb_checkpoints']:
        for f in glob.iglob(os.path.join(cwd, "**", d), recursive=True):
            if os.path.exists(f):
                os.system(f'rm -rf {f}')

if __name__ == '__main__':
    _do_clean()