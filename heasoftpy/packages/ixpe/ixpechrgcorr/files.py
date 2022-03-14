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

import os
import sys
import numpy

from astropy.io import fits

from .utils import current_datetime_string

import logging
#from logging_ import logger, abort


NOT_AVLB = 'N/A'

# Dictionary of correspondence between DET_ID and DETNAM for flight DUs
DETNAMS_DICT = {'DU_FM1' : 'DU4',
                'DU_FM2' : 'DU1',
                'DU_FM3' : 'DU2',
                'DU_FM4' : 'DU3'}

def det_label(detnam=NOT_AVLB, det_id=NOT_AVLB):
    """ Return a label corresponding to the the detector identifier. The label
    is 'dx' where x is equal to 1, 2, 3 or 4 for flight models and to a 2-digit
    number for other detectors (e.g. x = 29 for GPD 29).

    Parameters
    ----------
    detnam : string
        Logical name of the instrument (e.g. DU1)

    det_id : string
        Physical name of the instrument (e.g. DU_FM1 or GPD29)
    """
    if detnam == NOT_AVLB:
        if det_id == NOT_AVLB:
            return 'd0'
        else:
            if det_id.startswith('DU_FM'):
                detnam = DETNAMS_DICT[det_id]
                detnum = int(detnam[2])
            elif det_id.startswith('GPD'):
                detnum = int(det_id[3:5])
    else:
        detnum = int(detnam[2])
    return 'd%d' % detnum

def open_fits_file(file_path, **kwargs):
    """ Thin wrapper around astropy.fits.open, with the aim of performing a few
    basic checks on the file path.

    Parameters
    ----------
    file_path : string
        The input file path
    """

    logger = logging.getLogger('ixpechrgcorr')

    if not os.path.isfile(file_path):
#        abort('Cannot open input file %s' % file_path)
        logger.error('Cannot open input file %s' % file_path)
        sys.stdout.write('Cannot open input file %s' % file_path)
        sys.exit('Cannot open input file %s' % file_path)
    if not file_path.endswith('.fits'):
#        abort('Input file %s does not look like a FITS file' % file_path)
        logger.error('Input file %s does not look like a FITS file' % file_path)
        sys.stdout.write('Input file %s does not look like a FITS file' % file_path)
        sys.exit('Input file %s does not look like a FITS file' % file_path)
    logger.info('Opening input file %s...' % file_path)
#    sys.stdout.write('Opening input file %s...' % file_path)
    return fits.open(file_path, **kwargs)

def read_initial_charging_map(initial_map_file):
    """ Open the initial charging map file and read the values for the slow and
    fast component. We get the number of bins per side from the header.

    Parameters
    ----------
    initial_map_file : string
        the path to the input FITS file storing the charging map
    """

    logger = logging.getLogger('ixpechrgcorr')

    charging_map = open_fits_file(initial_map_file)['CHRG_MAP']
    nside = charging_map.header['NUM_BINS']
    # Initialize the initial slow and fast values as 2d arrays filled with zeroes
    initial_dg_fast = numpy.full((nside, nside), 0.)
    initial_dg_slow = numpy.full((nside, nside), 0.)
    # We fill the two arrays without doing any assumption on the order of the
    # values in the FITS files, but using explicitly the index from the BINX
    # and BINY columns. This is slower but safer, as it will work even if we
    # change the ordering in the input file.
    logger.info('Charging map has (%d x %d) bins' % (nside, nside))
    fast = charging_map.data['FAST']
    slow = charging_map.data['SLOW']
    binx = charging_map.data['BINX']
    biny = charging_map.data['BINY']
    for i, (x, y) in enumerate(zip(binx, biny)):
        # Note: indexes of numpy are (row, column), so y goes first
        initial_dg_fast[y, x] = fast[i]
        initial_dg_slow[y, x] = slow[i]
    return initial_dg_fast, initial_dg_slow

def read_charging_parameters(input_file_path):
    """Open a charging parameters calibration file, read the parameters and
    return them.

    Parameters
    ----------
    input_file_path : string
        the path to the input FITS file storing the charging parameters
    """
    extension = open_fits_file(input_file_path)['CHRG_PAR']
    params = extension.data[0]
    return params['KC_FAST'], params['TD_FAST'], params['DM_FAST'], \
           params['KC_SLOW'], params['TD_SLOW'], params['DM_SLOW']

def create_charging_map_extension(fast_map, slow_map, start_time=NOT_AVLB,
                                  start_date=NOT_AVLB, version=1, **keywords):
    """ Create the CHRG_MAP extension for a charging map file.

    Parameters
    ----------
    fast_map : numpy array
        a map of the fast component of the charging

    slow_map : numpy array
        a map of the slow component of the charging

    start_time : string
        the time of the day to which the map is referred to (fmt="%m/%d/%Y")

    start_date : string
        the date to which the map is referred to (fmt="%H:%M:%S")

    version : int
        version nuber of the extension

    keywords : dictionary [string] -> keyword
        a dictionary of kewyords that will be written in the header of the
        extension
    """
    # The shape of the fast and of the slow map must match
    if fast_map.shape[0] != slow_map.shape[0]:
        raise RuntimeError('Could not create the CHRG_MAP extension: '\
                           'fast and slow map shape mismatch! (%d != %d)' % \
                           (fast_map.shape[0], slow_map.shape[0]))
    # After the check it is safe to take the size from either of the maps
    nside = fast_map.shape[0]
    # We use numpy.tile and numpy.repeat to get the right sequence
    # respectively for the rows and the columns
    binx = fits.Column(name='BINX',
                       array=numpy.tile(numpy.arange(nside), nside),
                       format='I')
    biny = fits.Column(name='BINY',
                       array=numpy.repeat(numpy.arange(nside), nside),
                       format='I')
    slow = fits.Column(name='SLOW', array=slow_map.flatten(), format='D')
    fast = fits.Column(name='FAST', array=fast_map.flatten(), format='D')
    charging_hdu = fits.BinTableHDU.from_columns([binx, biny, fast, slow])
    # Additional keywords, specific of the charging extension
    charging_keywords = {
        'EXTNAME' : 'CHRG_MAP',
        'VERSION' : (version, 'Extension version number'),
        'CVSD0001' : (start_date, 'Date when this file should first be used'),
        'CVST0001' : (start_time, 'Time of day when this file should first be used'),
        'NUM_BINS' : (nside, 'Number of bins per side of the map'),
        'COMMENT' : 'This extension provides a map of the detector charging '\
                    'status expressed as a fraction of its maximum value.'
    }
    # Write the keywords into the header of the extension
    keywords.update(charging_keywords)
    for key, value in keywords.items():
        charging_hdu.header[key] = value
    return charging_hdu

def write_charging_map_to_file(output_file_path, fast_map, slow_map,
                               start_time=NOT_AVLB, start_date=NOT_AVLB,
                               detnam=NOT_AVLB, det_id=NOT_AVLB,
                               version=1, creator=NOT_AVLB):
    """ Write a map of the slow and fast charging to file. For the meaning of
    some of the arguments see the create_charging_map_extension() function

    Parameters
    ----------
    output_file_path : string
        path to the output file

    detnam : string
        detector unit logical name (e.g. DU1)

    det_id : string
        detector unit physical name (e.g. DU_FM2)
    """

    logger = logging.getLogger('ixpechrgcorr')

    # Create a PRIMARY HDU
    primary_hdu = fits.PrimaryHDU()
    # Define the keywords for the PRIMARY extension
#    current_date = current_datetime_string("%m/%d/%Y %H:%M:%S")
    current_date = current_datetime_string("%Y-%m-%dT%H:%M:%S.%f")
    primary_keywords = {
        'CREATOR'  : (creator, 'creator app'),
        'ORIGIN'   : ('IXPE Italy', 'Source of FITS file'),
        'DATE'     : (current_date, 'File creation date')
    }
    # Define the keywords common to the PRIMARY and the charging map extension
    shared_keywords = {
        'TELESCOP' : ('IXPE', 'Telescope (mission) name'),
        'INSTRUME' : ('GPD', 'Instrument name'),
        'DETNAM'  : (detnam, 'name of the logical Detector Unit'),
        'DET_ID'  : (det_id, 'name of the physical Detector Unit')
    }
    # Write both set of keywords into the header of the PRIMARY extension
    primary_keywords.update(shared_keywords)
    for key, value in primary_keywords.items():
        primary_hdu.header[key] = value
    # Now add the FILENAME keyword for the charging extension only:
    shared_keywords.update(
        {'FILENAME' : (os.path.basename(output_file_path), 'File name')}
                          )
    # Create the charging map extension
    charging_hdu = create_charging_map_extension(fast_map, slow_map,
        start_time=start_time, start_date=start_date, detnam=detnam,
        det_id=det_id, version=version, **shared_keywords)
    # Create the HDUList and write everything to file
    new_hdul = fits.HDUList([primary_hdu, charging_hdu])
    logger.info('Writing charging map to %s...', output_file_path)
    new_hdul.writeto(output_file_path, overwrite=True)
    logger.info('Done.')
    return output_file_path


def create_charging_parameter_file(output_file_path=None,
                                   detnam=NOT_AVLB, det_id=NOT_AVLB,
                                   start_date=None, start_time=None,
                                   version=1, creator=NOT_AVLB,
                                   **charging_parameters):
    """
    """

    logger = logging.getLogger('ixpechrgcorr')

    if output_file_path is None:
        du_label = det_label(detnam=detnam, det_id=det_id)
        output_file_path = 'ixpe_sample_%s_%s_chrgparams_%02d.fits' % \
                           (du_label, current_datetime_string("%Y%m%d"),
                           version)
#    date_ = current_datetime_string("%m/%d/%Y %H:%M:%S")
    date_ = current_datetime_string("%Y-%m-%dT%H:%M:%S.%f")
    if start_date is None:
        start_date = current_datetime_string("%m/%d/%Y")
    if start_time is None:
        start_time = current_datetime_string("%H:%M:%S")
    output_file_name = os.path.basename(output_file_path)
    keywords = {
        'TELESCOP' : ('IXPE', 'Telescope (mission) name'),
        'INSTRUME' : ('GPD', 'Instrument name'),
        'CREATOR' : (creator, 'creator app'),
        'ORIGIN' : ('IXPE Italy', 'Source of FITS file'),
        'DATE' : (date_, 'file creation date'),
        'DETNAM' : (detnam, 'Detector Unit Logical ID (1,2 or 3)'),
        'DET_ID' : (det_id, 'Name of the physical Detector Unit of the instr'),
    }
    primary_hdu = fits.PrimaryHDU()
    for key, value in keywords.items():
        primary_hdu.header[key] = value
    k_c_fast = fits.Column(name='KC_FAST',
        array=numpy.array([charging_parameters.get('k_c_fast')]), format='D')
    tau_d_fast = fits.Column(name='TD_FAST',
        array=numpy.array([charging_parameters.get('tau_d_fast')]), format='D')
    delta_max_fast = fits.Column(name='DM_FAST',
        array=numpy.array([charging_parameters.get('delta_max_fast')]),
        format='D')
    k_c_slow = fits.Column(name='KC_SLOW',
        array=numpy.array([charging_parameters.get('k_c_slow')]), format='D')
    tau_d_slow = fits.Column(name='TD_SLOW',
        array=numpy.array([charging_parameters.get('tau_d_slow')]), format='D')
    delta_max_slow = fits.Column(name='DM_SLOW',
        array=numpy.array([charging_parameters.get('delta_max_slow')]),
        format='D')
    chrg_params_hdu = fits.BinTableHDU.from_columns([k_c_fast, tau_d_fast,
                          delta_max_fast, k_c_slow, tau_d_slow, delta_max_slow])
    chrg_params_keywords = {
        'EXTNAME' : 'CHRG_PAR',
        'FILENAME' : (output_file_name, 'File name'),
        'VERSION' : (version, 'Extension version number'),
        'CONTENT' : ('IXPE Charging Parameters Files', 'File content'),
        'CCLS0001' : ('BCF', 'Dataset is a Basic Calibration File'),
        'CDTP0001' : ('DATA', 'Calibration file contains data'),
        'CCNM0001' : ('CHRG_PAR', 'Type of calibration data'),
        'CVSD0001' : (start_date, 'Date when this file should first be used'),
        'CVST0001' : (start_time, 'Time of day when this file should first be used'),
        'CDES0001' : ('IXPE Charging parameters', 'Description'),
        'COMMENT' : 'This extension provides the value of the parameters used '\
                    'in charging correction.'
    }
    keywords.update(chrg_params_keywords)
    for key, value in keywords.items():
        chrg_params_hdu.header[key] = value
    new_hdul = fits.HDUList([primary_hdu, chrg_params_hdu])
    logger.info('Writing charging parameters file %s...' % output_file_path)
    new_hdul.writeto(output_file_path, overwrite=True)
    logger.info('Done.')
