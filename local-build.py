import os
import glob
import argparse as argp
import subprocess
import sys
    
def _do_clean():
    """Removes the wrappers in heasoftpy/fcn and temporary files"""
    fcn = os.path.join('heasoftpy', 'fcn')
    print(f'cleaning wrappers in {fcn}')
    filelist = [f for f in os.listdir(fcn) if '.py' == f[-3:] and not f[:2] == '__']
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
    """Clear and build locally"""
    parser = argp.ArgumentParser(
        prog='clean-build',
        description='Clear and build heasoftpy locally into build folder',
    )
    parser.add_argument('-c', '--clean-only', dest='clean_only',
                        action='store_true',
                        help='clean only; do not build')
    args = parser.parse_args()

    # clean first by removing temporary files/folders
    _do_clean()

    if not args.clean_only:
        # call 'pip install'
        subprocess.check_call([
            sys.executable, 
            "-m", "pip", "install", ".", "--no-deps", "-t", "build"
        ])
