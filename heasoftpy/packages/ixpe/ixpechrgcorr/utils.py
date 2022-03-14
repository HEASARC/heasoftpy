#*****************************************************************************************************
# CONTAINS TECHNICAL DATA/COMPUTER SOFTWARE DELIVERED TO THE U.S. GOVERNMENT WITH UNLIMITED RIGHTS
#
# Contract No.: <Contract number, if applicable.>
# Contractor Name: <Space Science Data Center (SSDC), Italian Space Agency (ASI)>
# Contractor Address: <Via del Politecnico snc, 00133 Rome, Italy>
#
# Copyright 2018-2022 by <The Imaging X-ray Polarimetry Explorer (IXPE) team>. All rights reserved.
#
# Use by Non-US Government recipients is allowed by a BSD 3-Clause "Revised" Licensed detailed
# below:
#
# Developed by: <SSDC IXPE Team, INFN IXPE Team>
#               <SSDC-ASI, INFN, INAF>
#               <www.ssdc.asi.it, home.infn.it, www.inaf.it>
#
# Redistribution and use in source and binary forms, with or without modification, are permitted
# provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this list of
#    conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice, this list of
#    conditions and the following disclaimer in the documentation and/or other materials provided
#    with the distribution.
# 3. Neither the name of the copyright holder nor the names of its contributors may be used to
#    endorse or promote products derived from this software without specific prior written
#    permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND
# FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
# IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT
# OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#*****************************************************************************************************
from __future__ import print_function, division

import numpy
import datetime


def fixed_interval_time_binning(start_time, stop_time, time_interval,
                                adjust_stop=True):
    """Divide a time interval between a start and a stop in bins of fixed
    duration. The last bin can be optionally extended over the stop time in
    order to preserve the fixed size.

    Parameters
    ----------
    start_time : float
        The start time (in the same units as time_interval)

    stop_time : float
        The stop time (in the same units as time_interval)

    time_interval : int or float
        The requested amount of time per bin

    adjust_stop : bool
        Whether the edge of the last bin will be extended over the stop_time in
        order to preserve the correct size of the bins
    """
    num_bins = (stop_time - start_time) / time_interval
    # We need an integer number. If num_bins is not already an integer, round
    # it to the nearest greater integer
    if num_bins == int(num_bins):
        num_bins = int(num_bins)
    else:
        num_bins = int(num_bins) + 1
    # We extend the last bin over the stop time in order to preserve the
    # given number of seconds per bin
    if adjust_stop:
        stop_time = start_time + num_bins * time_interval
    return numpy.linspace(start_time, stop_time, num_bins + 1)

def bisect_binning(binning, values, **kwargs):
    """Return the indices corresponding to a give array of values for a
    given binning.

    Example
    -------
    >>> binning = numpy.linspace(0, 10, 11)
    >>> array([ 0.,  1.,  2.,  3.,  4.,  5.,  6.,  7.,  8.,  9., 10.])
    >>> bisect_binning(0.3)
    >>> 0
    >>> bisect_binning(9.9)
    >>> 9

    Parameters
    ----------
    binning : array
        the edges of the bin

    values : array
        the values which position is searched
    """
    return numpy.searchsorted(binning, values, **kwargs) - 1


"""The Unix time of the mission start (January 1, 2017)"""
MISSION_START_UNIX_TIME = 1483228800

"""Default datetime format string.
"""
DATETIME_FMT = '%Y-%m-%dT%H:%M:%S.%f'

def met_to_unix(met):
    """Convert a MET to a Unix time.

    Parameters
    ----
    met : float
        The input mission elapsed time.

    Returns
    -------
    float
        The Unix time corresponding to the input mission elapsed time.
    """
    return met + MISSION_START_UNIX_TIME

def unix_to_string(ut, tzinfo=datetime.timezone.utc, fmt=DATETIME_FMT):
    """Convert a Unix time to a string expressing time and date.

    Parameters
    ----
    ut : float
        The input Unix time.

    tzinfo : a datetime.timezone instance or None
        The timezone info (use None for local time).

    fmt : string
        The format for the output string

    Returns
    -------
    string
        The string corresponding to the input time
    """
    _datetime = datetime.datetime.fromtimestamp(ut, tzinfo)
    return _datetime.strftime(fmt)

def current_datetime_string(fmt=DATETIME_FMT):
    """ Return a string corresponding to the current time.

    Parameters
    ----
    fmt : string
        The format for the output string

    Returns
    -------
    string
        The string corresponding to the current time
    """
    return datetime.datetime.now().strftime(fmt)
