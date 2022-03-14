# CONTAINS TECHNICAL DATA/COMPUTER SOFTWARE DELIVERED TO THE U.S. GOVERNMENT WITH UNLIMITED RIGHTS
#
# Contract No.: CA 80MSFC17M0022
# Contractor Name: Universities Space Research Association
# Contractor Address: 7178 Columbia Gateway Drive, Columbia, MD 21046
#
# Copyright 2018-2022 by Universities Space Research Association (USRA). All rights reserved.
#
# Use by Non-US Government recipients is allowed by a BSD 3-Clause "Revised" Licensed detailed
# below:
#
# Developed by: William H. Cleveland Jr. and Erick A. Verleye
#               Universities Space Research Association
#               Science and Technology Institute
#               https://sti.usra.edu
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


import os
import sys
from typing import Tuple, List, Dict, Any

import numpy as np
from astropy.io import fits
from astropy.table import Table
from heasoftpy.fcn.quzcif import quzcif
from ..ixpeexpmap.ixpeexpmap_lib import GenericPixelMap
from ..orbit.cartesian import Quaternion, Vector
from ..time import Time
from scipy.interpolate import interp1d
import logging
from ..versioning import VERSION

from heasoftpy.core import HSPTask, HSPResult
SKYVIEW_WIDTH = 600
SKYVIEW_HEIGHT = 600


class Det2J2000Task(HSPTask):

    name = 'ixpedet2j2000'

    def exec_task(self):
        infile = self.params['infile']
        attitude = self.params['attitude']
        outfile = self.params['outfile']
        teldef = self.params['teldef']
        sc = self.params['sc'] in ['yes', 'y', True]
        clobber = self.params['clobber'] in ['yes', 'y', True]

        logger = logging.getLogger(self.name)

        ph = fits.getheader(infile, extname='Primary')

        if teldef == '-':
            obs_time = Time(ph['DATE-OBS'])
            tf = obs_time.strftime('%Y-%m-%d_%H:%M:%S')
            yymmdd = tf.split('_')[0]
            hhmmss = tf.split('_')[1]

            teldef = quzcif(mission='ixpe', instrument='xrt', codename='teldef', detector='-', filter='-',
                            date=yymmdd, time=hhmmss, expr='-').stdout.split(' ')[0]

            if teldef == '':
                err_str = 'No telescope definition CALDB file could be found for the input observation time.'
                logger.error(err_str)
                raise LookupError(err_str)

        telescope_header = fits.getheader(teldef)

        file_level = str(ph['FILE_LVL'])

        try:
            if file_level == '1':
                j2000_data = Lvl1Det2J2000(infile, attitude, telescope_header, sc)
            else:
                sys.exit(2)

        except KeyError:
            sys.exit(2)

        hdul = fits.open(infile)

        hdul['EVENTS'] = j2000_data.create_updated_hdu()

        date = Time.now().tt.fits
        for hdu in hdul:
            hdu.header['DATE'] = date

        if os.path.dirname(outfile) != '':
            os.makedirs(os.path.dirname(outfile), exist_ok=True)

        hdul.writeto(outfile, checksum=True, overwrite=clobber)

        hdul.close()

        outMsg, errMsg = self.logger.output
        return HSPResult(0, outMsg, errMsg, self.params)


def calc_j2000_x_y(event_ra: float, event_dec: float, target_ra: float, target_dec: float) -> tuple:
    """
    Calculates the event position RA and Dec on the sky tangent plane relative to the target
    Args:
        event_ra: Event RA in radians
        event_dec: Event Dec in radians
        target_ra: Target RA in radians
        target_dec: Target DEC in radians

    Returns:
        x_t (float): Event RA relative to target on the tangent plane
        y_t (float): Event Dec relative to the target on the tangent plane

    """
    x_t = np.sin(event_ra - target_ra) / (
            (np.sin(target_dec) * np.tan(event_dec)) + (np.cos(target_dec) * np.cos(event_ra - target_ra))
    )
    y_t = (np.tan(event_dec) - (np.tan(target_dec) * np.cos(event_ra - target_ra))) / (
            np.tan(target_dec) * np.tan(event_dec) + np.cos(event_ra - target_ra)
    )

    return x_t, y_t


class BaseDet2J2000:
    """
    Contains the methods required for processing all levels of event files.
    """

    def __init__(self, input_file_path: str, sc: bool = False):
        """
        Initializes the base attributes and methods.
        Args:
            input_file_path (str): Path to the Level-B/C Event file being processed.
            sc (bool): If true, spacecraft coordinates of the events are output to columns SCX, SCY. Set to false by
                       default.
        """
        self._input_file_path = input_file_path
        self._sc = sc
        self._input_table: Table = Table.read(self._input_file_path, hdu='EVENTS')
        self._original_header = fits.getheader(self._input_file_path, extname='EVENTS')

        self._du = fits.getheader(self._input_file_path, extname='Primary')['DETNAM'][-1]
        self._primary_header = fits.getheader(input_file_path, hdu='Primary')

        self._sorted_attitude_tables = None
        self._alignment_data = None
        self._telescope_defs = None
        self._gpm = None

    def _initialize_gpm(self):
        gpm = GenericPixelMap(
            SKYVIEW_WIDTH,
            SKYVIEW_HEIGHT,
            self._telescope_defs['DET_XSCL'],
            self._telescope_defs['DET_YSCL'],
            self._telescope_defs['SKY_XSCL'],
            self._telescope_defs['SKY_YSCL']
        )

        return gpm

    @property
    def _tstart(self) -> Time:
        """
        Finds the earliest time in the input Events file.
        Returns:
            t (Time): Astropy time object representing the earliest time in the input Events file.
        """
        t = Time(self._input_table['TIME'][0], scale='tt', format='ixpesecs')

        return t

    @property
    def _tstop(self) -> Time:
        """
        Finds the latest time in the input Events file.
        Returns:
            t (Time): Astropy time object representing the latest time in the input Events file.
        """
        t = Time(self._input_table['TIME'][-1], scale='tt', format='ixpesecs')

        return t

    def _retrieve_telescope_cal(self) -> Tuple[int, int, float]:
        """
        Uses the Caldb.indx file to lookup the valid telescope definitions for the current job.
        Returns:
            x_flip (int): Either 1 or -1. Indicates if the detector frame x-axis needs to be flipped.
            y_flip (int): Either 1 or -1. Indicates if the detector frame y-axis needs to be flipped.
            focal_length (float): Focal length of optics (mm).
        """
        x_flip = self._telescope_defs['DETXFLIP']
        y_flip = self._telescope_defs['DETYFLIP']
        focal_length = self._telescope_defs['FOCALLEN']

        return x_flip, y_flip, focal_length

    @staticmethod
    def _calc_attitude_vtis(attitude_table: Table, t_delt: float = 0.2) -> List[Tuple[float, float]]:
        """
        Find the time intervals in the attitude file for which there are no large gaps in time.
        Args:
            attitude_table: Table object containing TIME column and attitude data

        Returns:
            vtis (list): List of valid time intervals found within the input attitude table

        """
        vtis = []
        start = None
        stop = None
        tlast = None

        for time in attitude_table['TIME']:
            if start is None:
                start = time
            elif time - tlast > t_delt:
                vtis.append((start, stop))
                start = time

            stop = time
            tlast = time

        vtis.append((start, stop))
        return vtis

    @staticmethod
    def _calculate_interpolations(attitude_table: Table, vtis: List[Tuple[float, float]]) -> List[Dict[str, Any]]:
        """
        For each VTI in the overlapping attitude files, calculate an interpolation between the TIME and
        the row index.
        Returns:
            interps (list): The interpolations between TIME and row index for each attitude file VTI.
        """
        if 'TIME' in attitude_table.columns:
            attitude_table.add_index('TIME')
        else:
            return []

        interps = []
        for vti in vtis:
            start = vti[0]
            stop = vti[-1]

            if start <= attitude_table['TIME'][-1] and stop >= attitude_table['TIME'][0]:
                start_index = attitude_table.loc_indices[
                    attitude_table['TIME'][np.where(attitude_table['TIME'] >= start)][0]]
                stop_index = attitude_table.loc_indices[
                    attitude_table['TIME'][np.where(attitude_table['TIME'] <= stop)]
                    [-1]]

                f = interp1d(attitude_table['TIME'][start_index:stop_index + 1],
                             np.arange(start_index, stop_index + 1), kind='nearest')

                interps.append({
                    'start': attitude_table['TIME'][start_index],
                    'stop': attitude_table['TIME'][stop_index],
                    'start_index': start_index,
                    'stop_index': stop_index,
                    'interp': f
                })

        return interps

    def _calculate_j2000_x_y_index(self, event_ra: float, event_dec: float, target_ra: float, target_dec: float)\
            -> tuple:
        """
        Calculates the event position RA and Dec on the sky tangent plane relative to the target. Reflect the x-axis
        about the vertical axis.
        Args:
            event_ra: Event RA in radians
            event_dec: Event Dec in radians
            target_ra: Target RA in radians
            target_dec: Target DEC in radians

        Returns:
            x_t (float): Event horizontal pixel position
            y_t (float): Event vertical pixel position

        """
        x, y = calc_j2000_x_y(event_ra, event_dec, target_ra, target_dec)
        x, y = self._gpm.skyfield_to_index(np.rad2deg(x), np.rad2deg(y), places=3)
        x = (2 * ((SKYVIEW_WIDTH // 2) - 1)) - x

        return x, y


class Lvl1Det2J2000(BaseDet2J2000):
    def __init__(self, input_file_path, attitude_data: str, telescope_header: fits.header.Header, sc: bool = False):
        super().__init__(input_file_path, sc)
        self._telescope_defs = telescope_header
        self._x_flip, self._y_flip, self._focal_length = self._retrieve_telescope_cal()
        self._sorted_attitude_tables = sorted([file_path for file_path in attitude_data.split(',')],
                                              key=lambda x: fits.getheader(x, extname='Primary')['DATE'])
        self._tangent_plane_coords = None
        self._gpm = self._initialize_gpm()
        self._check_attitude_tables()
        self._tangent_plane_coords = self._calculate_tangent_plane_sky_coords()

    def _check_attitude_tables(self):
        radecs = []
        for attitude_path in self._sorted_attitude_tables:
            ph = fits.getheader(attitude_path, extname='Primary')
            radecs.append((ph['RA_OBJ'], ph['DEC_OBJ']))

        if not len(set(radecs)) == 1:
            raise ValueError('All input Attitude file must have same value for RA_OBJ and DEC_OBJ in primary header')

    @staticmethod
    def _create_radec_lookup(attitude_path, attitude_vtis):
        lookup = []
        ph = fits.getheader(attitude_path, extname='Primary')
        if 'RA_OBJ' not in ph.keys() or 'DEC_OBJ' not in ph.keys():
            raise LookupError('{}: RA_OBJ and DEC_OBJ need to be set in the Primary header'.format(attitude_path))
        else:
            for vti in attitude_vtis:
                lookup.append({
                    'start': vti[0],
                    'stop': vti[1],
                    'ra': np.deg2rad(ph['RA_OBJ']),
                    'dec': np.deg2rad(ph['DEC_OBJ'])
                })

        return lookup

    def _calculate_tangent_plane_sky_coords(self) -> Tuple[List[float], List[float], List[float], List[float]]:
        """
        Calculates the projection of the event positions onto the tangent plane centered on the target.
        Returns:
            x_t (list): The projections onto the J2000 x-axis of the tangent plane.
            y_t (list): The projections onto the J2000 y-axis of the tangent plane.
            x_sc_t (list): The spacecraft x-coordinates of each event.
            y_sc_t (list): The spacecraft y-coordinates of each event.
        """
        x_t = [np.NaN for i in range(len(self._input_table))]
        y_t = [np.NaN for i in range(len(self._input_table))]
        x_sc_t = [np.NaN for i in range(len(self._input_table))]
        y_sc_t = [np.NaN for i in range(len(self._input_table))]

        for file_path in self._sorted_attitude_tables:

            attitude_table = Table.read(file_path, hdu='HK')
            attitude_vtis = self._calc_attitude_vtis(attitude_table)
            att_interp = self._calculate_interpolations(attitude_table, attitude_vtis)
            radec_lookup = self._create_radec_lookup(file_path, attitude_vtis)

            for i, row in enumerate(self._input_table):

                # Check if j2000 solution has already been filled in by a newer aspect solution
                if not np.isnan(x_t[i]):
                    continue

                if bool(row['STATUS2'][0]) is True:  # No aspect solution flag
                    continue

                x = self._x_flip * row['ABSX']
                y = self._y_flip * row['ABSY']
                df_event_position = Vector(x=-x, y=-y, z=self._focal_length).normalize()

                t = row['TIME']

                # Find the correct interpolation to use. Any events that don't have an aspect solution should have been
                # filtered out by the STATUS2 value at the beginning of the loop
                interp_found = False
                for interp in att_interp:
                    if interp['start'] - 0.1 <= t <= interp['stop'] + 0.1:
                        if t < interp['start']:
                            q_dj = Quaternion(*attitude_table['QDJ'][interp['start_index']])
                            q_js = Quaternion(*attitude_table['QSJ_ST1'][interp['start_index']]).inverse()

                        elif t > interp['stop']:
                            q_dj = Quaternion(*attitude_table['QDJ'][interp['stop_index']])
                            q_js = Quaternion(*attitude_table['QSJ_ST1'][interp['stop_index']]).inverse()

                        else:
                            q_dj = Quaternion(*attitude_table['QDJ'][int(interp['interp'](t))])
                            q_js = Quaternion(*attitude_table['QSJ_ST1'][int(interp['interp'](t))]).inverse()

                        interp_found = True
                        break

                if not interp_found:
                    continue

                j2000_event_position = q_dj.rotate(df_event_position)
                event_ra, event_dec = j2000_event_position.to_radec()

                if self._sc:
                    sc = q_js.rotate(j2000_event_position)
                    x_sc_t[i] = sc.x
                    y_sc_t[i] = sc.y

                radec_found = False
                for interval in radec_lookup:
                    if interval['start'] - 0.1 <= t <= interval['stop'] + 0.1:
                        target_ra = interval['ra']
                        target_dec = interval['dec']

                        radec_found = True
                        break

                if not radec_found:
                    continue

                x, y = self._calculate_j2000_x_y_index(event_ra, event_dec, target_ra, target_dec)

                x_t[i] = x
                y_t[i] = y

            return x_t, y_t, x_sc_t, y_sc_t

    def create_updated_hdu(self) -> fits.BinTableHDU:
        """
        Replace the event positions in detector coordinates with the event positions in the J2000 frame.
        Returns:
            hdu (fits.BinTableHDU): The input HDU with the event positions appended in the J2000 frame.
        """
        hdul = fits.open(self._input_file_path)
        hdu = hdul['EVENTS']

        columns = []
        for colname in hdu.columns.names:
            if colname in ['X', 'Y'] or (self._sc and colname in ['SCX', 'SCY']):
                continue

            if colname in ['PIX_PHAS', 'PIX_PHAS_EQ']:
                columns.append(fits.Column(name=colname, format='QI()', array=np.array(hdu.data[colname],
                                                                                       dtype=np.object_)))
            else:
                columns.append(fits.Column(name=colname, format=hdu.columns[colname].format, array=hdu.data[colname],
                                           unit=hdu.columns[colname].unit, disp=hdu.columns[colname].disp,
                                           bzero=hdu.columns[colname].bzero))
        hdul.close()

        x_j2000 = fits.Column(array=self._tangent_plane_coords[0], name='X', format='D', unit='pixels')
        y_j2000 = fits.Column(array=self._tangent_plane_coords[1], name='Y', format='D', unit='pixels')

        columns.append(x_j2000)
        columns.append(y_j2000)

        if self._sc:
            x_sc = fits.Column(array=self._tangent_plane_coords[2], name='SCX', format='D', unit='pixels')
            y_sc = fits.Column(array=self._tangent_plane_coords[3], name='SCY', format='D', unit='pixels')
            columns.append(x_sc)
            columns.append(y_sc)

        cols = fits.ColDefs(columns)

        bin_table = fits.BinTableHDU.from_columns(cols, header=self._original_header)

        return bin_table


def ixpedet2j2000(args=None, **kwargs):
    """Transforms IXPE event positions and Stokes parameters
    from detector to sky coordinates.
    
    ixpedet2j2000 converts DETX, DETY detector coordinates and Stokes
    parameters DETQ and DETU of events contained in an existing Level 1
    IXPE event FITS file (infile) to X, Y sky coordinates and Q, U oriented
    along declination (+Q) and position angle (+U along position angle +45
    degrees) and adds these new columns, along with all original Level 1
    event file columns, to a new FITS file (outfile). Optionally, event
    positions in spacecraft coordinates can also be added to the output
    event FITS file (sc=true).

    ixpedet2j2000 uses the event time stamp from the Level 1 event list and
    the rotation quaternions from a Level 1 attitude file (attitude) to
    perform this transformation. The quaternions are calculated by
    combining time-independent quaternions representing detector frame to
    the focal plane frame, focal plane frame to the spacecraft frame, and
    spacecraft frame to star tracker optical head with the time-varying
    quaternions produced by the star tracker, which rotate from the star
    tracker optical head frame to the J2000 sky frame. The latter
    quaternions are generated at a rate of 10 Hz. The transformation
    quaternion is found by linearly interpolating between the two attitude
    solutions which bracket the event time component-by-component.
    
    
    Parameters:
    -----------
    infile* (str)
          Input FITS Event file.

    outfile* (str)
          Output file name.

    attitude* (str)
          FITS Attitude file corresponding to input Event file.

    teldef
          Path to the teldef CALDB file (default: -)

    sc
          Append column of event locations in spacecraft coordinates?
          (default: no)

    clobber
          Overwrite existing output file? (default: no)
          
    """
    det2j2000_task = Det2J2000Task('ixpedet2j2000')
    result = det2j2000_task(args, **kwargs)
    return result
