"""
Utilities for the heasoftpy module, generally intended for use by the module,
not called by users.
"""

import csv
import os
import subprocess
import sys

class ProgramVersion():
    """
    Methods for comparing version numbers, which allow use of the symbols less
    than (<), greater than (>), equals (=) and not equals (!=). The versions
    must be made up of only numeric digits and dots (periods), e.g. "6.9.42".
    Other characters will fail upon instantiation.
    """
    def __init__(self, ver):
        self.version = ver
        parts = self.version.split('.')
        self.ver_parts = list()
        for part in parts:
            try:
                self.ver_parts.append(int(part))
            except ValueError:
                err_msg = 'Error! Could not parse {0} (could not convert {1} to integer).'.\
                          format(self.version, part)
                sys.exit(err_msg)

    def __eq__(self, other):
        if len(self.ver_parts) == len(other.ver_parts):
            for ndx in range(len(self.ver_parts)):
                if self.ver_parts[ndx] != other.ver_parts[ndx]:
                    return False
        else:
            return False
        return True

    def __gt__(self, other):
        max_parts = max(len(self.ver_parts), len(other.ver_parts))
        for ndx in range(max_parts):
            if ndx < len(self.ver_parts):
                self_part = self.ver_parts[ndx]
            else:
                self_part = 0
            if ndx < len(other.ver_parts):
                other_part = int(other.ver_parts[ndx])
            else:
                other_part = 0
            if self_part > other_part:
                return True
        return False

    def __lt__(self, other):
        max_parts = max(len(self.ver_parts), len(other.ver_parts))
        for ndx in range(max_parts):
            if ndx < len(self.ver_parts):
                self_part = self.ver_parts[ndx]
            else:
                self_part = 0
            if ndx < len(other.ver_parts):
                other_part = int(other.ver_parts[ndx])
            else:
                other_part = 0
            if self_part < other_part:
                return True
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

def read_version(module_dir):
    """
    Returns a string containing the version, as read from the version file.
    """
    full_module_dir = os.path.abspath(module_dir)
    ver_str = None
    ver_path = os.path.join(full_module_dir, 'version')
    if os.path.exists(ver_path):
        with open(ver_path, 'rt') as ver_file:
            try:
                ver_str = str(ver_file.read())
            except:
                err_msg = 'Error! Could not read file "version" in the {} directory.'.\
                          format(full_module_dir)
                sys.exit(err_msg)
    else:
        err_msg = 'Error! Could not locate file "version" in the {} directory.'.\
                  format(full_module_dir)
        sys.exit(err_msg)
    return ver_str
