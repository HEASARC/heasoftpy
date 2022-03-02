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


import enum
import math
from typing import List, Tuple, Callable

import numpy as np
from astropy.io import fits
from astropy.table import Table, vstack
from heasoftpy.fcn.quzcif import quzcif
from ..fits.factory import PublicExposureMap
from ..time import Time
import logging
from heasoftpy.core import HSPTask, HSPResult


class PixelValue(enum.IntEnum):
    LIVE = 1
    UNUSABLE = 0


class GrayBadFlag(enum.IntEnum):
    LEFT = 4
    RIGHT = 5
    TOP = 6
    BOTTOM = 7
    INTERIOR = 8


class ExcBadFlag(enum.IntEnum):
    LEFT = 0
    RIGHT = 1
    TOP = 2
    BOTTOM = 3
    INTERIOR = 4


GRAY_BAD_FLAG_INDICES = [flag.value for flag in GrayBadFlag]
EXC_BAD_FLAG_INDICES = [flag.value for flag in ExcBadFlag]

SKY_MAP_WIDTH = 600  # Pixel space
SKY_MAP_HEIGHT = 600  # Pixel space

DETECTOR_WIDTH = 300  # Pixel space
DETECTOR_HEIGHT = 300  # Pixel space

ROTATION_THRESHOLD = np.pi / 4
SHEAR_THRESHOLD = 3 * np.pi / 4


VERSION = '1.1.0'


class ExpMapTask(HSPTask):

    name = 'ixpeexpmap'

    def exec_task(self):
        infile = self.params['infile']
        gti_file = self.params['gti']
        outfile = self.params['outfile']
        exclude_gray_pixels = self.params['exc_graypix'] in ['yes', 'y', True]
        teldef = self.params['teldef']
        badpix = self.params['badpix']
        use_corr = self.params['use_corr'] in ['yes', 'y', True]
        pointing_map = self.params['pntmap'] in ['yes', 'y', True]
        pointing_map_outfile = self.params['pntname']
        clobber = self.params['clobber'] in ['yes', 'y', True]

        logger = logging.getLogger(self.name)

        gti_table = Table.read(gti_file, hdu='GTI')
        obs_time = Time(gti_table[0]['START'], format='ixpesecs')
        tf = obs_time.strftime('%Y-%m-%d_%H:%M:%S')
        yymmdd = tf.split('_')[0]
        hhmmss = tf.split('_')[1]

        m = Level1MapBuilder(infile, use_corr=use_corr)

        detector = m.primary_header['DETNAM'][-1]
        obs_id = m.primary_header['OBS_ID']

        usable_aspect_solutions = m.parse_aspect_solutions(gti_table)

        bins = m.create_pa_bins(usable_aspect_solutions['PADY'],
                                m.primary_header['PADYN'])

        if teldef == '-':
            teldef = quzcif(mission='ixpe', instrument='xrt', codename='teldef', detector='-', filter='-',
                            date=yymmdd, time=hhmmss, expr='-').stdout.split(' ')[0]

            if teldef == '':
                raise LookupError('No telescope definition CALDB file could be found for first time found in HK HDU')

        if badpix == '-':
            badpix = quzcif(mission='ixpe', instrument='xrt', codename='badpix', detector='DU{}'.format(detector),
                            filter='-', date=yymmdd, time=hhmmss, expr='-').stdout.split(' ')[0]
            if badpix == '':
                raise LookupError(
                    'No bad pixel CALDB file could be found for DU{} for first time found in HK HDU'.format(detector))

        teldef = fits.getheader(teldef)
        badpix = Table.read(badpix, hdu='BADPIX')

        exposure_map = m.create_exposure_map(
            usable_aspect_solutions,
            teldef['DET_XSCL'],
            teldef['DET_YSCL'],
            teldef['SKY_XSCL'],
            teldef['SKY_YSCL'],
            teldef['XD1_D{}'.format(detector)],
            teldef['XD2_D{}'.format(detector)],
            teldef['YD1_D{}'.format(detector)],
            teldef['YD2_D{}'.format(detector)],
            badpix,
            bins,
            exclude_gray_pixels)

        if outfile == '-':
            outfile = 'ixpe{}_det{}_expmap.fits'.format(obs_id, detector)

        phdu = PublicExposureMap.from_hdu_data(
            level='2' if use_corr else '1',
            image_data=exposure_map.pixels,
            outfile=outfile,
            t_start=usable_aspect_solutions[0]['TIME'],
            t_stop=usable_aspect_solutions[-1]['TIME'],
            creator='ixpeexpmap',
            creator_id=VERSION,
            detector_name='DU{}'.format(detector),
            detector_id='DU_FM{}'.format(int(detector) + 1),
            observation_id=obs_id,
            on_time=sum([row['STOP'] - row['START'] for row in gti_table]),
            ra=m.primary_header['RA_OBJ'],
            dec=m.primary_header['DEC_OBJ'],
            sky_xscl=exposure_map._sky_xscl,
            sky_yscl=exposure_map._sky_yscl,
            image_width=SKY_MAP_WIDTH,
            image_height=SKY_MAP_HEIGHT
        )

        hdul = fits.HDUList([phdu])
        hdul.writeto(outfile, overwrite=clobber)

        logger.info('Exposure map written to {}'.format(outfile))

        if pointing_map:
            if pointing_map_outfile == '-':
                pointing_map_outfile = 'ixpe{}_det{}_pntmap.fits'.format(obs_id, detector)

            pointing_map = PointingDirectionMap(
                teldef['DET_XSCL'],
                teldef['DET_YSCL'],
                teldef['SKY_XSCL'],
                teldef['SKY_YSCL'],
                use_corr=use_corr
            )

            pointing_map.add_aspect_solutions(usable_aspect_solutions)

            phdu = PublicExposureMap.from_hdu_data(
                level='2' if use_corr else '1',
                image_data=pointing_map.pixels,
                outfile=pointing_map_outfile,
                t_start=usable_aspect_solutions[0]['TIME'],
                t_stop=usable_aspect_solutions[-1]['TIME'],
                creator='ixpeexpmap',
                creator_id=VERSION,
                detector_name='DU{}'.format(detector),
                detector_id='DU_FM{}'.format(int(detector) + 1),
                observation_id=obs_id,
                on_time=sum([row['STOP'] - row['START'] for row in gti_table]),
                ra=m.primary_header['RA_OBJ'],
                dec=m.primary_header['DEC_OBJ'],
                sky_xscl=exposure_map._sky_xscl,
                sky_yscl=exposure_map._sky_yscl,
                image_width=SKY_MAP_WIDTH,
                image_height=SKY_MAP_HEIGHT
            )

            hdul = fits.HDUList([phdu])
            hdul.writeto(pointing_map_outfile, overwrite=clobber)

            logging.info('Pointing map written to {}'.format(pointing_map_outfile))

        outMsg, errMsg = self.logger.output
        return HSPResult(0, outMsg, errMsg, self.params)


class GenericPixelMap:
    """
    A general purpose pixel map that is used as a base class for the Detector, Live Pixel, Pointing Direction,
    and Exposure maps.
    """
    __slots__ = ['pixels', '_width_offset', '_height_offset', '_det_xscl', '_det_yscl', '_sky_xscl', '_sky_yscl']

    def __init__(self, width: int, height: int, det_xscl: float, det_yscl: float, sky_xscl: float, sky_yscl: float):
        """
        Args:
            width (int): Width of the detector in pixels.
            height (int): Height of the detector in pixels.
            det_xscl (float): Pixel to mm conversion factor along horizontal axis.
            det_yscl (float): Pixel to mm conversion factor along vertical axis.
            sky_xscl (float): Pixel to degree conversion factor along J2000 horizontal axis.
            sky_yscl (float): Pixel to degree conversion factor along J2000 vertical axis.
        """
        self.pixels = np.zeros((height, width), dtype=np.float32)
        self._width_offset = (width // 2) - 1
        self._height_offset = (height // 2) - 1
        self._det_xscl = det_xscl
        self._det_yscl = det_yscl
        self._sky_xscl = sky_xscl
        self._sky_yscl = sky_yscl

    def _index_to_pixel(self, i: int, j: int, offset=None, phi=None) -> (int, int):
        """
        Transforms the array index to a pixel location.
        Args:
            i (int): Column index of the pixel in the pixel array.
            j (int): Row index of the pixel in the pixel array.
        """
        x_pixel = i - self._width_offset
        y_pixel = j - self._height_offset

        if phi is not None:
            x_pixel, y_pixel = self._rotate(x_pixel, y_pixel, phi)
            x_pixel = round(x_pixel)
            y_pixel = round(y_pixel)

        if offset is not None:
            x_pixel += offset[0]
            y_pixel += offset[1]

        return x_pixel, y_pixel

    def _pixel_to_index(self, x: int, y: int):
        """
        Transforms a pixel coordinate to its corresponding pixel array address.
        Args:
            x (int): Horizontal component of the point in pixel space
            y (int): Vertical component of the point in pixel space
        Returns:
            i, j (int, int): The pixel array address.
        """
        i = int(x + self._width_offset)
        j = int(y + self._height_offset)

        return i, j

    def skyfield_to_index(self, x: float, y: float, places: int = 0):
        """
        Transforms a point in skyfield space to its pixel array address.
        Args:
            x (float): Horizontal component of the point on skyfield plane (deg).
            y (float): Vertical component of the point on skyfield plane (deg).
            places (int): The amount of places to round to
        Returns:
            i, j (int, int): The pixel array address.
        """
        first_pixel_x = (self._sky_xscl * self._width_offset) + (self._sky_xscl / 2)
        first_pixel_y = (self._sky_yscl * self._width_offset) + (self._sky_yscl / 2)

        i = round((x + first_pixel_x) / self._sky_xscl, places)
        j = round((y + first_pixel_y) / self._sky_yscl, places)

        return i, j

    def physical_to_index(self, x: float, y: float, operation: Callable = round):
        """
        Transforms a coordinate point in physical space to its pixel array address.
        Args:
            x (float): Horizontal component of the point in physical space (mm)
            y (float): Vertical component of the point in physical space (mm)
            operation (func): Mathematical operation which defines the conversion
        Returns:
            i, j (int, int): The pixel array address.
        """
        first_pixel_x = (self._det_xscl * self._width_offset) + (self._det_xscl / 2)
        first_pixel_y = (self._det_yscl * self._height_offset) + (self._det_yscl / 2)

        i = operation((x + first_pixel_x) / self._det_xscl)
        j = operation((y + first_pixel_y) / self._det_yscl)

        return i, j

    def pixel_to_physical(self, x: int, y: int, phi: float = None, offset: (float, float) = None) -> (float, float):
        """
        Transforms a coordinate point in pixel space to a physical point.
        Args:
            x (int): Horizontal component of the point in pixel space
            y (int): Vertical component of the point in pixel space
            phi (float): The angle by which to rotate the pixel about the center of the map.
            offset (float, float): Optional offset to translate the physical location by.
        Returns:
            x, y (float, float): The point in physical coordinates.
        """
        x_phy = self._det_xscl * (x - 0.5)
        y_phy = self._det_yscl * (y - 0.5)

        if phi is not None:
            x_phy, y_phy = self._rotate(x_phy, y_phy, phi)

        if offset is not None:
            x_phy += offset[0]
            y_phy += offset[1]

        return x_phy, y_phy

    def pixel_to_skyfield(self, x: int, y: int, phi: float = None, offset: (float, float) = None) -> (float, float):
        """
        Transforms a coordinate point in pixel space to a skyfield point.
        Args:
            x (int): Horizontal component of the point in pixel space
            y (int): Vertical component of the point in pixel space
            phi (float): The angle by which to rotate the pixel about the center of the map.
            offset (float, float): Optional offset to translate the physical location by.
        Returns:
            x_sky, y_sky (float, float): The point in skyfield coordinates.
        """
        x_sky = self._sky_xscl * (x - 0.5)
        y_sky = self._sky_yscl * (y - 0.5)

        if phi is not None:
            x_sky, y_sky = self._rotate(x_sky, y_sky, phi)

        if offset is not None:
            x_sky += offset[0]
            y_sky += offset[1]

        return x_sky, y_sky

    def _rotate(self, x: float, y: float, phi: float, places=0) -> (float, float):
        """
        Rotates a point about the origin by a given angle.
        Args:
            x (float): Original position on the horizontal axis.
            y (float): Original position on the vertical axis.
            phi (float): The angle by which to rotate the pixel about the center of the map.
        """
        # Shearing degenerates when rotating two quadrants away in one pass, split it up into two rotations
        if -1 <= np.cos(phi) < np.cos(SHEAR_THRESHOLD):
            x, y = self._rotate(x, y, SHEAR_THRESHOLD)
            phi = (phi % (2 * np.pi)) % SHEAR_THRESHOLD

        tangent = np.tan(phi / 2)

        # Shear 1
        x_new = round(x + y * tangent, places)

        # Shear 2
        y_new = round(x_new * -np.sin(phi) + y, places)

        # Shear 3
        x_new = round(x_new + y_new * tangent, places)

        return x_new, y_new


class DetectorMap(GenericPixelMap):
    """
    Defines an array of Pixel objects that represent a detector. Each pixel has value 1 (live), 0 (unusable), -1 (dead).
    This class also contains methods for translating, rotating, and adding the map.
    """

    def __init__(self, det_xscl: float, det_yscl: float, sky_xscl: float, sky_yscl: float,
                 x_min: float, x_max: float, y_min: float, y_max: float, badpix: Table, exclude_gray_pixels: bool):
        """
        Args:
            det_xscl (float): Pixel to mm conversion factor along horizontal axis.
            det_yscl (float): Pixel to mm conversion factor along vertical axis.
            sky_xscl (float): Pixel to degree conversion factor along J2000 horizontal axis.
            sky_yscl (float): Pixel to degree conversion factor along J2000 vertical axis.
            x_min (float): The minimum usable dimension in mm of the horizontal axis.
            x_max (float): The maximum usable dimension in mm of the horizontal axis.
            y_min (float): The minimum usable dimension in mm of the vertical axis.
            y_max (float): The maximum usable dimension in mm of the vertical axis.
            badpix (Table): Defines the location of the bad pixels of the detector.
            exclude_gray_pixels (bool): True if the pixels defined as "gray" will have their values set to -1, and thus
            treated as dead pixels.
        """
        super().__init__(DETECTOR_WIDTH, DETECTOR_HEIGHT, det_xscl, det_yscl, sky_xscl, sky_yscl)

        # Turn on the pixels within the usable dimensions of the detector, flip the axes because of projection onto the
        # sky
        bottom_left = self.physical_to_index(x_min, y_min, operation=math.ceil)
        top_right = self.physical_to_index(x_max, y_max, operation=math.floor)
        self.pixels[bottom_left[1]:top_right[1], bottom_left[0]:top_right[0]] = PixelValue.LIVE.value

        for row in badpix:
            bad_flag = row['BADFLAG']
            indices = row['DET_PY'], row['DET_PX']
            exc_flag = any(bool(bad_flag[index]) for index in EXC_BAD_FLAG_INDICES)
            gray_flag = any(bool(bad_flag[index]) for index in GRAY_BAD_FLAG_INDICES)

            if exc_flag or (exclude_gray_pixels and gray_flag):
                self.pixels[indices] = PixelValue.UNUSABLE.value

    def _index_to_pixel(self, i: int, j: int, offset=None, phi=None) -> (int, int):
        """
        Transforms the array index to a pixel location.
        Args:
            i (int): Column index of the pixel in the pixel array.
            j (int): Row index of the pixel in the pixel array.
        """
        # Reflect the indexes over the axes of the detector
        # The x-axis is reflected once through the MMA, and then once again for a view "from inside" the celestial
        # sphere, thus the index to pixel conversion in x is unchanged
        x_pixel = i - self._width_offset
        y_pixel = self._height_offset - j + 1

        if phi is not None:
            x_pixel, y_pixel = self._rotate(x_pixel, y_pixel, phi)
            x_pixel = round(x_pixel)
            y_pixel = round(y_pixel)

        if offset is not None:
            x_pixel += offset[0]
            y_pixel += offset[1]

        return x_pixel, y_pixel


class LivePixelMap(GenericPixelMap):
    """
    Defines an array of Pixel objects that represent the live pixels of a detector map projected onto a skyfield.
    Each pixel has value 1 (live), 0 (unusable), -1 (dead). This class also contains methods for translating, rotating,
    and adding to the map.
    """

    def __init__(self, det_xscl: float, det_yscl: float, sky_xscl: float, sky_yscl: float):
        """
        Args:
            det_xscl (float): Pixel to mm conversion factor along horizontal axis.
            det_yscl (float): Pixel to mm conversion factor along vertical axis.
            sky_xscl (float): Pixel to degree conversion factor along J2000 horizontal axis.
            sky_yscl (float): Pixel to degree conversion factor along J2000 vertical axis.
        """
        super().__init__(SKY_MAP_WIDTH, SKY_MAP_HEIGHT, det_xscl, det_yscl, sky_xscl, sky_yscl)

    def add_map(self, other, phi: float = None, offset: List[float] = None):
        """
        Adds another map to the LivePixelMap (LPM) object by first finding the nearest neighbor of any bad pixels on
        'other' and indicating those as dead on the 'self' map. Then a perimeter polygon is made from the corner live
        pixels of 'other' map and any 'self' pixels that are contained by the polygon and aren't dead are turned on.
        Args:
            other: Pixel map to be added to the self.
            offset: Horizontal and vertical offset of the other map from self center in skyfield degrees.
            phi: Rotation angle of the other map in radians. Positive angle -> CW rotation
        """
        if isinstance(other, DetectorMap):
            if offset is not None:
                offset[0] = -offset[0]  # Positive offsets on the sky are to the left
                offset = self._index_to_pixel(*self.skyfield_to_index(*offset))

            usable_pixels = [
                other._index_to_pixel(x_index, y_index, offset=offset, phi=phi)
                for x_index in range(DETECTOR_WIDTH)
                for y_index in range(DETECTOR_HEIGHT)
                if other.pixels[y_index, x_index] == PixelValue.LIVE.value
            ]

            for pixel in usable_pixels:
                i, j = self._pixel_to_index(*pixel)
                if 0 <= i < SKY_MAP_WIDTH and 0 <= j < SKY_MAP_HEIGHT:
                    self.pixels[j, i] = PixelValue.LIVE.value

            return usable_pixels

        else:
            return NotImplemented


class PointingDirectionMap(GenericPixelMap):
    """
    Defines an array of Pixel objects that represent the unique pointing directions of the detector over a certain
    period. The pixel is either 0 or the time in seconds that the detector pointing vector is fixed on the pixel.
    """

    def __init__(self, det_xscl: float, det_yscl: float, sky_xscl: float, sky_yscl: float, use_corr: bool = False):
        """
        Args:
            det_xscl (float): Pixel to mm conversion factor along horizontal axis.
            det_yscl (float): Pixel to mm conversion factor along vertical axis.
            sky_xscl (float): Pixel to degree conversion factor along J2000 horizontal axis.
            sky_yscl (float): Pixel to degree conversion factor along J2000 vertical axis.
            use_corr (bool): If True TXYDZ_CORR column will be used for pointing centers
        """
        super().__init__(SKY_MAP_WIDTH, SKY_MAP_HEIGHT, det_xscl, det_yscl, sky_xscl, sky_yscl)
        self._use_corr = use_corr

    def add_aspect_solutions(self, aspect_solutions: Table, solution_period: float = 1 / 10):
        """
        Finds the nearest neighbor of each unique pointing direction and sets the value of that pixel to how long the
        specified detector is pointing in that direction.
        Args:
            aspect_solutions (Table): The aspect solutions that will be be added to the pointing map.
            solution_period (float): How long each solution period is valid for.
        """
        unique_offsets = {}
        for solution in aspect_solutions:

            if self._use_corr:
                x = solution['TXYDZ_CORR'][0]
                y = solution['TXYDZ_CORR'][1]

                if np.isnan(x) or np.isnan(y):
                    continue

            else:
                x = -np.rad2deg(solution['TXYDZ'][0])  # Positive offsets on the sky are to the left
                y = np.rad2deg(solution['TXYDZ'][1])

                if np.isnan(x) or np.isnan(y):
                    continue

                x, y = self._index_to_pixel(*self.skyfield_to_index(float(x), float(y)))

            offset = (x, y)
            if offset in unique_offsets.keys():
                unique_offsets[offset] += solution_period

            else:
                unique_offsets[offset] = solution_period

        pointing_centers = []
        for index, solution_offset in enumerate(unique_offsets):
            pointing_centers.append((unique_offsets[solution_offset], solution_offset[0], solution_offset[1]))

            i, j = self._pixel_to_index(solution_offset[0], solution_offset[1])
            if 0 <= i < SKY_MAP_WIDTH and 0 <= j < SKY_MAP_HEIGHT:
                self.pixels[j, i] = unique_offsets[solution_offset]

        return pointing_centers


class ExposureMap(GenericPixelMap):
    """
    Defines an array of Pixel objects that represent the time the detector has spent gathering information from each
    pixel projected onto the sky (the exposure).
    """

    def __init__(self, det_xscl: float, det_yscl: float, sky_xscl: float, sky_yscl: float):
        """
        Args:
            det_xscl (float): Pixel to mm conversion factor along horizontal axis.
            det_yscl (float): Pixel to mm conversion factor along vertical axis.
            sky_xscl (float): Pixel to degree conversion factor along J2000 horizontal axis.
            sky_yscl (float): Pixel to degree conversion factor along J2000 vertical axis.
        """
        super().__init__(SKY_MAP_WIDTH, SKY_MAP_HEIGHT, det_xscl, det_yscl, sky_xscl, sky_yscl)

    def add_pointing_and_live_pixel(self, pointing_centers: List[Tuple], live_pixels: List[Tuple]):
        """
        Add the live pixel map to the exposure map by re-centering the exposure map onto each non-zero pointing
        direction pixel. A polygon indicating the perimeter of the live pixels in the live pixel map is
        created and used to increment the exposure map pixels that are contained within it.
        Args:
            pointing_centers (List): List indicating the positions of the pointing directions in pixel space.
            live_pixels (List): List indicating the positions of the live pixels in pixel space.
        """
        for center_pixel in pointing_centers:
            for pixel in live_pixels:
                x = pixel[0] + center_pixel[1]
                y = pixel[1] + center_pixel[2]

                i, j = self._pixel_to_index(x, y)
                if 0 <= i < SKY_MAP_WIDTH and 0 <= j < SKY_MAP_HEIGHT:
                    self.pixels[j, i] += center_pixel[0]


class BaseMapBuilder:
    """
    Base class for creating the exposure map from Level-B and Level-1 Attitude data.
    """
    def __init__(self, use_corr: bool = False):
        self.attitude_table = None
        self._use_corr = use_corr

    @staticmethod
    def _calculate_position_angle_std(usable_position_angles: List[float]) -> float:
        """
        Calculates the standard deviation of the population of the input position angles.
        Args:
            usable_position_angles (list): The population of position angles to find the standard deviation of.
        """
        return np.std(usable_position_angles)

    def create_pa_bins(self, usable_position_angles: List[float], nominal_pa: float,
                       t_thresh: float = ROTATION_THRESHOLD) -> List[List[float]]:
        """
        Calculates the bin sizes of the position angles based on the standard deviation of the population of position
        angles. If the standard deviation is below the threshold given, then there is only one bin which contains all of
        the given position angles. If not, the bins are centered on the nominal position angle value and incremented
        by multiples of the threshold.
        Args:
            usable_position_angles (list): The position angles to be binned.
            nominal_pa (float): The nominal position angle of the detector.
            t_thresh (float): The standard deviation threshold given to determine whether the position angles need to
            be binned or not.
        """
        stddev = self._calculate_position_angle_std(usable_position_angles)

        if stddev <= t_thresh:
            bins = [
                [min(usable_position_angles),
                 max(usable_position_angles)]
            ]

        else:
            def find_n(n=2):
                if stddev <= (t_thresh * ((2 * n) + 1)):
                    return n
                return find_n(n + 1)

            N = find_n()
            ks = np.arange(-2 * N, (2 * N) + 1, 1)

            bins = [
                [
                    (nominal_pa + (2 * k * t_thresh)) - t_thresh,
                    (nominal_pa + (2 * k * t_thresh)) + t_thresh
                ] for k in ks
            ]

            bins.insert(0, [nominal_pa - np.pi, nominal_pa - 4 * N * t_thresh - t_thresh])
            bins.insert(len(bins), [nominal_pa + 4 * N * t_thresh + t_thresh, nominal_pa + np.pi])

        return bins

    def create_exposure_map(self, usable_aspect_solutions: Table, det_xscl: float, det_yscl: float, sky_xscl: float,
                            sky_yscl: float, x_min: float, x_max: float, y_min: float, y_max: float, badpix: Table,
                            start_time: Time, n_pa: float, bins: List[List[float]],
                            exclude_gray_pixels: bool) -> ExposureMap:
        """
        Initializes an exposure map, and then for each position angle bin a live pixel map and pointing direction map
        are created and added to the exposure map. The exposure map data is then written to a FITS file.
        Args:
            usable_aspect_solutions (Table): The aspect solutions that can be used with the input nominal offset and
            nominal position angle.
            det_xscl (float): Pixel to mm conversion factor along horizontal axis.
            det_yscl (float): Pixel to mm conversion factor along vertical axis.
            sky_xscl (float): Pixel to degree conversion factor along J2000 horizontal axis.
            sky_yscl (float): Pixel to degree conversion factor along J2000 vertical axis.
            x_min (float): The minimum usable dimension in mm of the horizontal axis.
            x_max (float): The maximum usable dimension in mm of the horizontal axis.
            y_min (float): The minimum usable dimension in mm of the vertical axis.
            y_max (float): The maximum usable dimension in mm of the vertical axis.
            badpix (Table): Defines the location of the bad pixels of the detector.
            start_time (Time): What time to use for caldb lookup.
            n_pa (float): The position angle of the detector's nominal rotation about the target center.
            bins (list): The bins for which to group the position angles in the usable aspect solutions.
            exclude_gray_pixels (bool): If True, gray pixels will be indicated as "dead" when making the live pixel map.
        """
        exp_map = ExposureMap(det_xscl, det_yscl, sky_xscl, sky_yscl)

        for pa_bin in bins:
            detector_map = DetectorMap(det_xscl, det_yscl, sky_xscl, sky_yscl, x_min, x_max, y_min, y_max, badpix,
                                       exclude_gray_pixels)
            pointing_direction_map = PointingDirectionMap(det_xscl, det_yscl, sky_xscl, sky_yscl,
                                                          use_corr=self._use_corr)
            live_pixel_map = LivePixelMap(det_xscl, det_yscl, sky_xscl, sky_yscl)

            # Standard deviation of the position angles was low enough to use nominal position angle for exposure
            # map creation
            if len(bins) == 1:
                pointing_centers = pointing_direction_map.add_aspect_solutions(usable_aspect_solutions)
                live_pix_indices = live_pixel_map.add_map(detector_map, -n_pa)
                exp_map.add_pointing_and_live_pixel(pointing_centers, live_pix_indices)

            else:
                bin_aspect_solutions = [
                    solution for solution in usable_aspect_solutions if
                    not np.isnan(solution['PADY']) and
                    pa_bin[0] <= solution['PADY'] <= pa_bin[1]
                ]
                bin_aspect_table = Table(rows=bin_aspect_solutions, names=usable_aspect_solutions.colnames)
                pa_bin_angle = np.mean(pa_bin)
                live_pix_indices = live_pixel_map.add_map(detector_map, -pa_bin_angle)
                pointing_centers = pointing_direction_map.add_aspect_solutions(bin_aspect_table)
                exp_map.add_pointing_and_live_pixel(pointing_centers, live_pix_indices)

            del detector_map, live_pixel_map, pointing_direction_map

        return exp_map


class Level1MapBuilder(BaseMapBuilder):
    """
    Class for creating the exposure map from Level-1 data.
    """

    def __init__(self, level_1_attitude_file: str, use_corr: bool = False):
        """
        Args:
            level_1_attitude_file (str): The data providing the aspect solutions for a single observation segment.
        """
        super().__init__(use_corr=use_corr)
        self.primary_header = fits.getheader(level_1_attitude_file, extname='Primary')
        self.attitude_table = Table.read(level_1_attitude_file, hdu='HK')

    def parse_aspect_solutions(self, lvl2_gti_table: Table) -> Table:
        """
        Uses the Level-2 GTI file corresponding to the input Level-1 Attitude file's observation segment ID and parses
        out the aspect solutions contained within these GTI.
        """
        parsed_attitude_table = vstack([
            self.attitude_table[
                np.where(
                    np.logical_and(
                        self.attitude_table['TIME'] >= row['START'],
                        self.attitude_table['TIME'] <= row['STOP']
                    )
                )
            ]
            for row in lvl2_gti_table
        ], metadata_conflicts='silent')

        return parsed_attitude_table

    def create_exposure_map(self, usable_aspect_solutions: Table, det_xscl: float, det_yscl: float, sky_xscl: float,
                            sky_yscl: float, x_min: float, x_max: float, y_min: float, y_max: float, badpix: Table,
                            bins: List[List[float]], exclude_gray_pixels: bool) -> ExposureMap:
        """
        Initializes an exposure map, and then for each position angle bin a live pixel map and pointing direction map
        are created and added to the exposure map. The exposure map data is then written to a FITS file.
        Args:
            usable_aspect_solutions (Table): The aspect solutions that can be used to create the exposure map (the
            solutions that are within the Level-2 GTI for this detector and observation segment)
            det_xscl (float): Pixel to mm conversion factor along horizontal axis.
            det_yscl (float): Pixel to mm conversion factor along vertical axis.
            sky_xscl (float): Pixel to degree conversion factor along J2000 horizontal axis.
            sky_yscl (float): Pixel to degree conversion factor along J2000 vertical axis.
            x_min (float): The minimum usable dimension in mm of the horizontal axis.
            x_max (float): The maximum usable dimension in mm of the horizontal axis.
            y_min (float): The minimum usable dimension in mm of the vertical axis.
            y_max (float): The maximum usable dimension in mm of the vertical axis.
            badpix (Table): Defines the location of the bad pixels of the detector.
            bins (list): The bins for which to group the position angles in the usable aspect solutions.
            exclude_gray_pixels (bool): If True, gray pixels will be indicated as "dead" when making the live pixel map.
        """
        exp_map = super().create_exposure_map(
            usable_aspect_solutions,
            det_xscl,
            det_yscl,
            sky_xscl,
            sky_yscl,
            x_min,
            x_max,
            y_min,
            y_max,
            badpix,
            Time(self.attitude_table['TIME'][0], format='ixpesecs'),
            self.primary_header['PADYN'],
            bins,
            exclude_gray_pixels
        )

        return exp_map


def ixpeexpmap(args=None, **kwargs):
    """Creates an exposure map in J2000 tangent-plane coordinates from the 
    aspect solution data in the Level 1 housekeeping data.
    
    ixpeexpmap selects the J2000 tangent-plane positions of the pointing
    direction from a Level 1 Attitude file (infile) for all the valid rows
    within Good Time Intervals read from a GTI file (gti) to create a
    pointing map (pntmap; default=false, if pntmap=true then the pointing
    map will be placed in an output file given by the parameter pntname).

    The pointing map contains standard sky tangent-plane X, Y coordinates
    with the value at each coordinate given by the exposure time in
    seconds. ixpeexpmap then calculates a valid pixel map to be convolved
    with the pointing map to create the final exposure map. The valid pixel
    map flags bad pixels and âgrayâ pixels (if graypix=true) from a bad
    pixel map (badpix). ixpeexpmap then convolves these two maps to build
    the final exposure map (outfile) using the appropriate rotations,
    offsets, and pixel-to-sky scalings (as given in the file teldef)
    necessary to convert raw pixels to sky coordinates. Exposure maps for
    multiple detectors can be co-added as differences in orientation and
    offset due to relative telescope pointing have already been accounted
    for.
    
    
    Parameters:
    -----------
    infile* (str)
          Input FITS Attitude file.

    gti* (str)
          Good Time Interval FITS file .

    outfile* (str)
          Output exposure map file name.

    exc_graypix
          Exclude gray pixels from exposure? (default: no)

    teldef
          Path to the teldef CALDB file (default: -)

    badpix
          Path to the badpix CALDB file (default: -)

    pntmap
          Output a skymap of the detector centers? (default: no)

    pntname
          Output exposure map file name (default: -)
          
    clobber
          Overwrite existing output file? (default: no)

    use_corr
          Use TXYDZ_CORR column for detector pointing centers? (default:no)
    
    """
    expmap_task = ExpMapTask('ixpeexpmap')
    result = expmap_task(args, **kwargs)
    return result
