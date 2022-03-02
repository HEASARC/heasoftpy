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
import re
from ..versioning import VERSION, HEA_VERSION, RELEASE_DATE
from astropy.io import fits
from astropy.time import Time
import numpy as np
from typing import Union


class BaseFitsFactory:
    """
    Contains the shared values and methods for writing both Housekeeping and Science FITS files
    """
    CALDBVER = None

    # Header Cards
    MJDREFI = (57754, 'start mission MJD (integer part)')
    MJDREFF = (0.00080074074074, 'start mission MJD (fractional part)')
    TELESCOPE = ('IXPE', 'Telescope or mission, IXPE')
    ORIGIN = ('MSFC', 'Location where the FITS file was created')  # TODO: Define this value as a function of FileType
    TIMESYS = ('TT', '')
    TIMEUNIT = ('s', '')

    # Header Comments
    TSTART_COMMENT = 'Observation start time in IXT, relative to MJDREF'
    TSTOP_COMMENT = 'Observation end time in IXT, relative to MJDREF'
    TELAPSE_COMMENT = 'Elapsed time, TSTOP-TSTART'
    DATE_OBS_COMMENT = '[TT] Date of start of observation in isot format'
    DATE_END_COMMENT = '[TT] Date of end of observation in isot format'
    CREAT_ID_COMMENT = 'Version of software that created the file'
    CREATOR_COMMENT = 'Software that produced the file'
    DATE_COMMENT = 'FITS File creation date'
    INSTRUMENT_COMMENT = 'Instrument of the telescope'
    FILETYPE_COMMENT = 'Brief description of the data type'
    OBS_ID_COMMENT = 'Observation ID'
    DETNAM_COMMENT = 'Name of the Detector Unit of the instrument'
    DET_ID_COMMENT = 'Name of the physical ID of the detector which corresponds to the given DETNAM'

    ONTIME_COMMENT = '[s] Engineering-defined exposure time, minus any intervals of science data not received on the' \
                     ' ground.'
    LIVETIME_COMMENT = '[s] Sum of LIVETIME column for valid GTI'
    DEADC_COMMENT = 'The ratio of LIVETIME/ONTIME values'
    DEADAPP_COMMENT = 'Flag indicating if dead time correction has been applied'

    RA_COMMENT = 'Right Ascension of target in J2000'
    DEC_COMMENT = 'Declination of target in J2000'
    FILE_LVL_COMMENT = 'Level of file of this type'
    FILE_TYP_COMMENT = 'File type'
    FILENAME_COMMENT = 'Name of this file'

    RADECSYS_COMMENT = 'Celestial coordinate system'
    EQUINOX_COMMENT = 'Equinox of celestial coordinate system'

    def _set_caldbver(self):
        """Set CALDBVER"""
        if self.CALDBVER is None:
            cif_header = fits.getheader(os.path.join(os.environ.get('CALDB'), 'data', 'ixpe', 'gpd', 'caldb.indx'),
                                        extname='CIF')
            self.CALDBVER = (cif_header['CALDBVER'],
                             'Version of the Calibration index that gives the calibration file list used during'
                             ' processing')

    def create_primary_hdu(self, outfile: str, t_start: float, t_stop: float, creator: str, creator_id: str,
                           header=None) -> fits.PrimaryHDU:
        """
        Base primary hdu to be used by both HK and Science files.
        Args:
            outfile (FileType): The FileType object of the overall FITS file.
            t_start (float): For Level-1 data, start time of the observation segment in ixpesecs. For intermediate
            files, the first valid time found in the file.
            t_stop (float): For Level-1 data, end time of the observation segment in ixpesecs. For intermediate
            files, the last valid time found in the file.
            creator_id (str): Version of the program that created the FITS file the HDU will be in.
            creator (str): Name of the program that created the FITS file the HDU will be in.
            header (fits.header.Header) (optional): The header to be used as a base for the HDU.
        Returns:
            primary_hdu (fits.PrimaryHDU): The base primary HDU for Science and HK files.
        """
        self._set_caldbver()
        primary_hdu = fits.PrimaryHDU(header=header)

        ixpe_date_obs = Time(t_start, format='ixpesecs', scale='tt')
        ixpe_date_end = Time(t_stop, format='ixpesecs', scale='tt')

        primary_hdu.header['TELESCOP'] = self.TELESCOPE
        primary_hdu.header['TIMESYS'] = self.TIMESYS
        primary_hdu.header['TIMEUNIT'] = self.TIMEUNIT
        primary_hdu.header['MJDREFI'] = self.MJDREFI
        primary_hdu.header['MJDREFF'] = self.MJDREFF
        primary_hdu.header['ORIGIN'] = self.ORIGIN

        primary_hdu.header['FILENAME'] = (os.path.basename(outfile).split('.fits')[0], self.FILENAME_COMMENT)
        primary_hdu.header['TSTART'] = (ixpe_date_obs.value, self.TSTART_COMMENT)
        primary_hdu.header['TSTOP'] = (ixpe_date_end.value, self.TSTOP_COMMENT)
        primary_hdu.header['TELAPSE'] = (round(ixpe_date_end.value - ixpe_date_obs.value, 6), self.TELAPSE_COMMENT)
        primary_hdu.header['DATE-OBS'] = (ixpe_date_obs.isot, self.DATE_OBS_COMMENT)
        primary_hdu.header['DATE-END'] = (ixpe_date_end.isot, self.DATE_END_COMMENT)
        primary_hdu.header['CREAT_ID'] = (creator_id, self.CREAT_ID_COMMENT)
        primary_hdu.header['CREATOR'] = (creator, self.CREATOR_COMMENT)
        primary_hdu.header['CALDBVER'] = self.CALDBVER

        return primary_hdu

    def _create_data_hdu(self, cols: fits.ColDefs, extname: str, t_start: float, t_stop: float,
                         header=None) -> fits.BinTableHDU:
        """
        Base data HDU to be used for all FITS file data extensions.
        Args:
            cols (fits.ColDefs): Columns of the FITS file.
            extname (str): Name of the extension.
            t_start (float): For Level-1 data, start time of the observation segment in ixpesecs. For intermediate
            files, the first valid time found in the file.
            t_stop (float): For Level-1 data, end time of the observation segment in ixpesecs. For intermediate
            files, the last valid time found in the file.
            header (fits.header.Header) (optional): The header to be used as a base for the HDU.
        Returns:
            data_hdu (fits.BinTableHDU): Data extension to be used in the FITS file.
        """
        self._set_caldbver()
        data_hdu = fits.BinTableHDU.from_columns(cols, name=extname, header=header)
        ixpe_date_obs = Time(t_start, format='ixpesecs', scale='tt')
        ixpe_date_end = Time(t_stop, format='ixpesecs', scale='tt')
        data_hdu.header['TSTART'] = (ixpe_date_obs.value, self.TSTART_COMMENT)
        data_hdu.header['TSTOP'] = (ixpe_date_end.value, self.TSTOP_COMMENT)
        data_hdu.header['TELAPSE'] = (round(ixpe_date_end.value - ixpe_date_obs.value, 6), self.TELAPSE_COMMENT)
        data_hdu.header['DATE-OBS'] = (ixpe_date_obs.isot, self.DATE_OBS_COMMENT)
        data_hdu.header['DATE-END'] = (ixpe_date_end.isot, self.DATE_END_COMMENT)

        data_hdu.header['MJDREFI'] = self.MJDREFI
        data_hdu.header['MJDREFF'] = self.MJDREFF
        data_hdu.header['ORIGIN'] = self.ORIGIN
        data_hdu.header['TELESCOP'] = self.TELESCOPE
        data_hdu.header['TIMESYS'] = self.TIMESYS
        data_hdu.header['TIMEUNIT'] = self.TIMEUNIT
        data_hdu.header['CALDBVER'] = self.CALDBVER

        return data_hdu

    def _create_gti_hdu(self, starts: list, stops: list, t_start: float, t_stop: float,
                        header=None) -> fits.BinTableHDU:
        """
        Creates a valid Good Time Intervals extension to be used in all FITS files.
        Args:
            starts (list): The start(s) of the GTI(s).
            stops (list): The stop(s) of the GTI(s).
            t_start (float): For Level-1 data, start time of the observation segment in ixpesecs. For intermediate
            files, the first valid time found in the file.
            t_stop (float): For Level-1 data, end time of the observation segment in ixpesecs. For intermediate
            files, the last valid time found in the file.
            header (fits.header.Header) (optional): The header to be used as a base for the HDU.
        Returns:
            gti_hdu (fits.BinTableHDU): Data extension with Good Time Intervals found in the file
        """
        self._set_caldbver()
        gti_cols = list()
        gti_cols.append(fits.Column(name='START', format='D',
                                    array=np.array(starts), unit='s'))
        gti_cols.append(fits.Column(name='STOP', format='D',
                                    array=np.array(stops), unit='s'))
        gti_columns = fits.ColDefs(gti_cols)

        gti_hdu = fits.BinTableHDU.from_columns(gti_columns, name="GTI", header=header)

        ixpe_date_obs = Time(t_start, format='ixpesecs', scale='tt')
        ixpe_date_end = Time(t_stop, format='ixpesecs', scale='tt')

        gti_hdu.header['TSTART'] = (ixpe_date_obs.value, self.TSTART_COMMENT)
        gti_hdu.header['TSTOP'] = (ixpe_date_end.value, self.TSTOP_COMMENT)
        gti_hdu.header['TELAPSE'] = (round(ixpe_date_end.value - ixpe_date_obs.value, 6), self.TELAPSE_COMMENT)
        gti_hdu.header['DATE-OBS'] = (ixpe_date_obs.isot, self.DATE_OBS_COMMENT)
        gti_hdu.header['DATE-END'] = (ixpe_date_end.isot, self.DATE_END_COMMENT)

        gti_hdu.header['MJDREFI'] = self.MJDREFI
        gti_hdu.header['MJDREFF'] = self.MJDREFF
        gti_hdu.header['ORIGIN'] = self.ORIGIN
        gti_hdu.header['TELESCOP'] = self.TELESCOPE
        gti_hdu.header['TIMESYS'] = self.TIMESYS
        gti_hdu.header['TIMEUNIT'] = self.TIMEUNIT
        gti_hdu.header['CALDBVER'] = self.CALDBVER

        return gti_hdu

    def write_fits(self, hdu_list: fits.HDUList, outfile: str, clobber=True) -> fits.HDUList:
        """
        Writes an engineering data FITS file in the directory specified.
        Args:
            hdu_list (fits.HDUList): Includes the required Primary HDU and any extensions.
            outfile (str): Output file name object.
            clobber (bool): True by default. If false FITS files with the same path will not be overwritten
        Returns:
            hdu_list (fits.HDUList): Includes the required Primary HDU and any extensions
        """
        # Update the date header cards
        file_date = Time.now().tt.fits
        for hdu in hdu_list:
            hdu.header['DATE'] = (file_date, self.DATE_COMMENT)

        hdu_list.writeto(outfile, overwrite=clobber, checksum=True)

        return hdu_list

    def __repr__(self) -> str:
        """Return a representation of the BaseFitsFactory object"""
        return "BaseTFParamFactory()"


class PublicHDU:
    TLM2FITS = (VERSION, 'Software version number in the form AA.BB, where AA is the major version and BB is the minor'
                         ' version.')
    PROCVER = ("00.02", 'Processing version')
    SOFTVER = ("Hea_{}_IXPE_{}_{}".format(HEA_VERSION, RELEASE_DATE, VERSION), 'HEASOFT and IXPE specific software'
                                                                               ' version string')
    LV1_VER = (5, 'Required for backward compatibility')
    LV2_VER = (1, 'The version of the LV2 file format')

    # TODO: Define OBSERVER comment
    OBSERVER_COMMENT = ""

    @classmethod
    def from_private_hdu(cls, hdu) -> Union[fits.PrimaryHDU, fits.BinTableHDU]:
        hdu.header['PROCVER'] = cls.PROCVER
        hdu.header['SOFTVER'] = cls.SOFTVER
        hdu.header['TLM2FITS'] = cls.TLM2FITS

        return hdu


class SkyMap(BaseFitsFactory):

    @classmethod
    def from_hdu_data(cls, image_data: np.ndarray, outfile: str, t_start: float, t_stop: float, creator: str,
                      creator_id: str, ra: float, dec: float, sky_xscl: float, sky_yscl: float, image_width: int,
                      image_height: int, unit: str) -> fits.PrimaryHDU:
        primary_hdu = cls().create_primary_hdu(outfile, t_start, t_stop, creator, creator_id)

        primary_hdu.data = image_data

        primary_hdu.header['BUNIT'] = (unit, 'Units of image array values')

        primary_hdu.header['CTYPE1'] = ('RA---TAN', 'Horizontal axis coordinate type')
        primary_hdu.header['CRPIX1'] = (image_width / 2, 'Array location of the horizontal reference point in pixels')
        primary_hdu.header['CRVAL1'] = (ra, 'Array value at horizontal reference point')
        primary_hdu.header['CDELT1'] = (-sky_xscl, 'Coordinate increment on horizontal axis')
        primary_hdu.header['CROTA1'] = (0.0, 'Rotation of horizontal axis at reference point')
        primary_hdu.header['CUNIT1'] = ('deg', 'Units of CDELT1 and CRVAL1')

        primary_hdu.header['CTYPE2'] = ('DEC--TAN', 'Vertical axis coordinate type')
        primary_hdu.header['CRPIX2'] = (image_height / 2, 'Array location of the vertical reference point in pixels')
        primary_hdu.header['CRVAL2'] = (dec, 'Array value at vertical reference point')
        primary_hdu.header['CDELT2'] = (sky_yscl, 'Coordinate increment on vertical axis')
        primary_hdu.header['CROTA2'] = (0.0, 'Rotation of vertical axis at reference point')
        primary_hdu.header['CUNIT2'] = ('deg', 'Units of CDELT2 and CRVAL2')

        primary_hdu = PublicHDU.from_private_hdu(primary_hdu)

        return primary_hdu

    def _create_data_hdu(self, cols: fits.ColDefs, extname: str, t_start: float, t_stop: float,
                         header=None) -> None:
        return None

    def _create_gti_hdu(self, starts: list, stops: list, t_start: float, t_stop: float,
                        header=None) -> None:
        return None


class FieldOfView(SkyMap):

    @classmethod
    def from_hdu_data(cls, image_data: np.ndarray, outfile: str, t_start: float,
                      t_stop: float, creator: str, creator_id: str, ra: float, dec: float, pay: float,
                      frame: str, sky_xscl: float, sky_yscl: float, image_width: int, image_height: int,
                      header=None) -> fits.PrimaryHDU:
        primary_hdu = super().from_hdu_data(image_data, outfile, t_start, t_stop, creator, creator_id,
                                            ra, dec, sky_xscl, sky_yscl, image_width, image_height, 'counts')
        primary_hdu.header['PAY'] = (pay, 'Position angle of spacecraft Y-axis from the target in J2000 coordinates')
        primary_hdu.header['RADECSYS'] = (frame, cls.RADECSYS_COMMENT)

        return primary_hdu


class BaseExposureFactory(SkyMap):
    XMAP_VERSION = 1
    EQUINOX = 2000.0
    RADECSYS = 'ICRS'

    @classmethod
    def from_hdu_data(cls, image_data: np.ndarray, outfile: str, t_start: float,
                      t_stop: float, creator: str, creator_id: str, detector_name: str, detector_id: str,
                      ra: float, dec: float, sky_xscl: float, sky_yscl: float, image_width: int, image_height: int
                      ) -> fits.PrimaryHDU:
        primary_hdu = super().from_hdu_data(image_data, outfile, t_start, t_stop, creator, creator_id,
                                            ra, dec, sky_xscl, sky_yscl, image_width, image_height, 'seconds')

        primary_hdu.header['INSTRUME'] = ('GPD', cls.INSTRUMENT_COMMENT)
        primary_hdu.header['DETNAM'] = (detector_name, cls.DETNAM_COMMENT)
        primary_hdu.header['DET_ID'] = (detector_id, cls.DET_ID_COMMENT)
        primary_hdu.header['XMAP_VER'] = cls.XMAP_VERSION
        primary_hdu.header['BITPIX'] = -32
        primary_hdu.header['NAXIS'] = 2
        primary_hdu.header['NAXIS1'] = image_width
        primary_hdu.header['NAXIS2'] = image_height
        primary_hdu.header['EQUINOX'] = (cls.EQUINOX, cls.EQUINOX_COMMENT)
        primary_hdu.header['RADECSYS'] = (cls.RADECSYS, cls.RADECSYS_COMMENT)
        primary_hdu.header['HDUCLASS'] = ('OGIP', 'format conforms to OGIP standard')
        primary_hdu.header['HDUCLAS1'] = ('IMAGE', '2-D image array')

        return primary_hdu


class PublicExposureMap(BaseExposureFactory):

    @classmethod
    def from_hdu_data(cls, level: str, image_data: np.ndarray, outfile: str, t_start: float, t_stop: float,
                      creator: str, creator_id: str, detector_name: str, detector_id: str, observation_id: str,
                      ra: float, dec: float, sky_xscl: float, sky_yscl: float, on_time: float, image_width: int,
                      image_height: int) -> fits.PrimaryHDU:
        primary_hdu = super().from_hdu_data(image_data, outfile, t_start, t_stop,
                                            creator, creator_id, detector_name, detector_id,
                                            ra, dec, sky_xscl, sky_yscl, image_width, image_height)

        primary_hdu.header['FILETYPE'] = (f'ENG EXPOSURE {level}', cls.FILETYPE_COMMENT)
        primary_hdu.header['OBS_ID'] = (observation_id, cls.OBS_ID_COMMENT)
        primary_hdu.header['ONTIME'] = (on_time, cls.ONTIME_COMMENT)

        return primary_hdu


def update_comments(header: fits.Header):
    ttype = r'TTYPE(?P<colnum>\d+)'
    tform = r'TFORM(?P<colnum>\d+)'
    tdisp = r'TDISP(?P<colnum>\d+)'
    tunit = r'TUNIT(?P<colnum>\d+)'
    tdim = r'TDIM(?P<colnum>\d+)'
    tnull = r'TNULL(?P<colnum>\d+)'
    tscal = r'TSCAL(?P<colnum>\d+)'
    tzero = r'TZERO(?P<colnum>\d+)'

    format_map = {
        'L': 'LOGICAL',
        'I': '2-byte INTEGER',
        'J': '4-byte INTEGER',
        'K': '8-byte INTEGER',
        'X': 'BIT',
        'E': '4-byte REAL',
        'D': '8-byte DOUBLE'
    }

    for card in header:
        match = re.match(ttype, card)
        if match:
            params = match.groupdict()
            header[card] = (header[card], 'label for field  {}'.format(params['colnum']))
            continue

        match = re.match(tdisp, card)
        if match:
            params = match.groupdict()
            header[card] = (header[card], 'display format for field {}'.format(params['colnum']))
            continue

        match = re.match(tdim, card)
        if match:
            params = match.groupdict()
            header[card] = (header[card], 'dimensions of field  {}'.format(params['colnum']))
            continue

        match = re.match(tnull, card)
        if match:
            params = match.groupdict()
            header[card] = (header[card], 'value that indicates undefined for field {}'.format(params['colnum']))
            continue

        elif re.match(tform, card):
            if header[card][0] in ['Q', 'P']:
                header[card] = (header[card], 'data format of field: variable length array')
            else:
                header[card] = (header[card], 'data format of field: {}'.format(format_map[header[card][-1]]))

        elif re.match(tunit, card):
            header[card] = (header[card], 'physical unit of field')

        elif re.match(tscal, card):
            if header[card] == 1:
                header[card] = (1, 'data are not scaled')
            else:
                header[card] = (header[card], 'data scaled by factor {}'.format(header[card]))

        elif re.match(tzero, card):
            header[card] = (header[card], 'offset for unsigned integers')

    return header
