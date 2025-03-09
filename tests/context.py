# -*- coding: utf-8 -*-

import sys
import os
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../build')))

import heasoftpy  # noqa 401

# set the global allow_failure for the tests
heasoftpy.Config.allow_failure = True
