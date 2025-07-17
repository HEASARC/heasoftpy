import os
import glob
import argparse as argp
import subprocess
import sys


def _do_clean():
    """Removes the wrappers in heasoftpy and temporary files"""
    temp_py = ['fcn.py', '_modules.py']
    modules = [d for d in glob.glob('heasoftpy/*')
               if os.path.isdir(d) or os.path.basename(d) in temp_py]
    for module in modules:
        print(f'cleaning wrappers in {module}')
        os.system(f'rm -rf {module}')
    for d in ['build', 'heasoftpy.egg-info', '__pycache__', 'dist',
              'heasoftpy-install.log', '.pytest_cache', 'pip.log',
              '.eggs', '*.pyc', '.ipynb_checkpoints']:
        if os.path.exists(d):
            os.system(f'rm -rf {d}')


if __name__ == '__main__':
    """Clear and build locally"""
    parser = argp.ArgumentParser(
        prog='clean-build',
        description='Clear and build heasoftpy locally into build folder',
    )
    parser.add_argument('-c', '--clean-only', dest='clean_only',
                        action='store_true',
                        help='clean only; do not build')
    parser.add_argument('-v', '--verbose', dest='verbose',
                        action='store_true',
                        help='print debug messages')
    args = parser.parse_args()

    # clean first by removing temporary files/folders
    _do_clean()

    if not args.clean_only:
        # call 'pip install'
        subprocess.check_call([
            sys.executable,
            "-m", "pip", "install", ".", "--no-deps", "-t", "build",
            "--log", "pip.log"
        ] + (["-v"] if args.verbose else []))
