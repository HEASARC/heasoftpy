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

import math
import os
from typing import Tuple
import logging

import numpy as np
from astropy import units as u
from astropy.coordinates import Angle, SkyCoord, get_sun, GCRS
from astropy.io import fits
from astropy.table import Table
from heasoftpy.fcn.quzcif import quzcif
from ..ixpeexpmap.ixpeexpmap_lib import DetectorMap, LivePixelMap, SKY_MAP_WIDTH, SKY_MAP_HEIGHT
from ..fits.factory import FieldOfView
from ..orbit.cartesian import Vector, Quaternion
from ..time import Time
from scipy.spatial.transform import Rotation
from heasoftpy.core import HSPTask, HSPResult

THRESH_ANGLE_DEG = 25.0
THRESH_ANGLE = Angle(THRESH_ANGLE_DEG, unit='deg')
SEP_MIN = Angle(90 - THRESH_ANGLE_DEG, unit='deg')
SEP_MAX = Angle(90 + THRESH_ANGLE_DEG, unit='deg')
Y_POINTING_THRESH = math.radians(THRESH_ANGLE_DEG)


VERSION = '1.1.0'


class CalcFOVTask(HSPTask):

    name = 'ixpecalcfov'

    def exec_task(self):
        observation_time = self.params['time']
        target_ra = self.params['ra']
        target_dec = self.params['dec']
        outfile = self.params['outfile']
        roll_angle = self.params['roll']
        refframe = self.params['refframe']
        align = self.params['align']
        teldef = self.params['teldef']
        badpix1 = self.params['badpix1']
        badpix2 = self.params['badpix2']
        badpix3 = self.params['badpix3']
        exclude_gray_pix = self.params['exc_graypix'] in ['yes', 'y', True]
        use_d1 = self.params['use_d1'] in ['yes', 'y', True]
        use_d2 = self.params['use_d2'] in ['yes', 'y', True]
        use_d3 = self.params['use_d3'] in ['yes', 'y', True]
        clobber = self.params['clobber'] in ['yes', 'y', True]

        logger = logging.getLogger(self.name)

        if roll_angle in ['no', 'n', False]:
            roll_angle = None
        else:
            roll_angle = Angle(roll_angle, unit=u.deg)

        obs_time = Time(observation_time)
        tf = obs_time.strftime('%Y-%m-%d_%H:%M:%S')
        yymmdd = tf.split('_')[0]
        hhmmss = tf.split('_')[1]

        target_ra = Angle(target_ra, unit=u.deg)
        target_ra.wrap_at(180 * u.deg, inplace=True)
        target_dec = Angle(target_dec, unit=u.deg)

        if align == '-':
            align = quzcif(mission='ixpe', instrument='xrt', codename='alignment', detector='-', filter='-',
                           date=yymmdd, time=hhmmss, expr='-').stdout.split(' ')[0]

            if align == '':
                err_str = 'No alignment CALDB file could be found for the input observation time.'
                logger.error(err_str)
                raise LookupError(err_str)

        alignment_data = Table.read(align, hdu='SYSTEM ALIGNMENT')

        if teldef == '-':
            teldef = quzcif(mission='ixpe', instrument='xrt', codename='teldef', detector='-', filter='-',
                            date=yymmdd, time=hhmmss, expr='-').stdout.split(' ')[0]

            if teldef == '':
                err_str = 'No telescope definition CALDB file could be found for the input observation time.'
                logger.error(err_str)
                raise LookupError(err_str)

        telescope_header = fits.getheader(teldef)

        badpix_paths = {}

        if use_d1:
            if badpix1 == '-':
                badpix1 = quzcif(mission='ixpe', instrument='xrt', codename='badpix', detector='DU1',
                                 filter='-', date=yymmdd, time=hhmmss, expr='-').stdout.split(' ')[0]
                if badpix1 == '':
                    err_str = 'No bad pixel CALDB file could be found for DU1 for the input observation time'
                    logger.error(err_str)
                    raise LookupError(err_str)

            badpix_paths['1'] = badpix1

        if use_d2:
            if badpix2 == '-':
                badpix2 = quzcif(mission='ixpe', instrument='xrt', codename='badpix', detector='DU2',
                                 filter='-', date=yymmdd, time=hhmmss, expr='-').stdout.split(' ')[0]
                if badpix2 == '':
                    err_str = 'No bad pixel CALDB file could be found for DU2 for the input observation time'
                    logger.error(err_str)
                    raise LookupError(err_str)

            badpix_paths['2'] = badpix2

        if use_d3:
            if badpix3 == '-':
                badpix3 = quzcif(mission='ixpe', instrument='xrt', codename='badpix', detector='DU3',
                                 filter='-', date=yymmdd, time=hhmmss, expr='-').stdout.split(' ')[0]
                if badpix3 == '':
                    err_str = 'No bad pixel CALDB file could be found for DU3 for the input observation time'
                    logger.error(err_str)
                    raise LookupError(err_str)

            badpix_paths['3'] = badpix3

        desired_attitude_quaternion, pay = calculate_desired_attitude_quat(obs_time, target_ra, target_dec, roll_angle,
                                                                           ref_frame=refframe)

        lpm = LivePixelMap(
            telescope_header['DET_XSCL'],
            telescope_header['DET_YSCL'],
            telescope_header['SKY_XSCL'],
            telescope_header['SKY_YSCL']
        )

        target = SkyCoord(ra=target_ra, dec=target_dec, frame=refframe)

        for detector in badpix_paths:
            # Detector to Focal Plane
            q_df = Quaternion(*alignment_data['Q_FP_DU{}'.format(detector)][0])

            # Mirror center / Detector center offset
            q_fm = Quaternion(*alignment_data['Q_FP_TEL{}'.format(detector)][0])

            # Focal plane to spacecraft
            q_sf = Quaternion(*alignment_data['Q_SC_FP'][0])

            q_ds = q_sf * q_fm * q_df

            # Spacecraft to desired reference frame
            q_dj = desired_attitude_quaternion * q_ds

            det = SkyCoord(*Angle(list(q_dj.rotate(Vector(0, 0, 1)).to_radec()), unit=u.rad), frame=refframe)

            scy_ra, scy_dec = q_dj.rotate(Vector(0, 1, 0)).to_radec()
            sc_pay = target.position_angle(
                SkyCoord(ra=Angle(scy_ra, unit=u.rad), dec=Angle(scy_dec, unit=u.rad), frame=refframe)
            )

            theta_z = -sc_pay.rad

            badpix_data = Table.read(badpix_paths[detector])

            dm = DetectorMap(
                telescope_header['DET_XSCL'],
                telescope_header['DET_YSCL'],
                telescope_header['SKY_XSCL'],
                telescope_header['SKY_YSCL'],
                telescope_header['XD1_D{}'.format(detector)],
                telescope_header['XD2_D{}'.format(detector)],
                telescope_header['YD1_D{}'.format(detector)],
                telescope_header['YD2_D{}'.format(detector)],
                badpix_data,
                exclude_gray_pix)

            sep = target.separation(det)
            pa = target.position_angle(det)
            lpm.add_map(dm, offset=[np.rad2deg(sep.rad * np.sin(pa.rad)), np.rad2deg(sep.rad * np.cos(pa.rad))],
                        phi=theta_z)

        # End of loop, all detector maps added to lpm
        if outfile == '-':
            if refframe != 'icrs':
                outfile = os.path.join(os.getcwd(), '{}_{}_{}_{}_fov.fits'.format(
                    round(target_ra.deg, 5), round(target_dec.deg, 5), obs_time.strftime('%Y%m%d_%H%M%S'),
                    refframe
                ))
            else:
                outfile = os.path.join(os.getcwd(), '{}_{}_{}_fov.fits'.format(
                    round(target_ra.deg, 5), round(target_dec.deg, 5), obs_time.strftime('%Y%m%d_%H%M%S')
                ))

        phdu = FieldOfView.from_hdu_data(
            image_data=lpm.pixels,
            outfile=outfile,
            t_start=obs_time.ixpesecs,
            t_stop=obs_time.ixpesecs,
            creator='ixpecalcfov',
            creator_id=VERSION,
            ra=round(target_ra.deg, 5),
            dec=round(target_dec.deg, 5),
            pay=round(pay.rad, 5),
            frame=refframe,
            sky_xscl=lpm._sky_xscl,
            sky_yscl=lpm._sky_yscl,
            image_width=SKY_MAP_WIDTH,
            image_height=SKY_MAP_HEIGHT,
        )

        hdul = fits.HDUList([phdu])
        hdul.writeto(outfile, overwrite=clobber)
        logger.info("Field of View map written to {}".format(outfile))

        outMsg, errMsg = self.logger.output
        return HSPResult(0, outMsg, errMsg, self.params)


def calculate_desired_attitude_quat(observation_time: Time, target_ra: Angle, target_dec: Angle,
                                    roll_angle: Angle = None, ref_frame: str = 'icrs') -> Tuple[Quaternion, Angle]:
    """
    Creates a quaternion that transforms from the spacecraft frame to J2000. This quaternion satisfies two conditions:
    1.) The spacecraft z-axis is pointing at the intended target.
    2.) The spacecraft y-axis (pointing direction of solar panels) is pointing at the sun.
    Args:
        observation_time (Time): The time of the intended observation.
        target_ra (Angle): Right Ascension of the target in degrees.
        target_dec (Angle): Declination of the target in degrees.
        roll_angle (Angle): User specified rotation of the spacecraft about the detector pointing axis in degrees.
        ref_frame (str): The reference frame of the target coordinates. This is also the frame that the output
        quaternion will transform spacecraft coordinates into.
    Returns:
        desired_attitude_quaternion (Quaternion): Quaternion that nominally transforms the spacecraft pointing axis
        to the desired target in the input reference frame.
    """
    observation_time = Time(observation_time)

    ref_target = SkyCoord(ra=target_ra, dec=target_dec, frame=ref_frame)
    gcrs_target = ref_target.transform_to(GCRS(obstime=observation_time))
    sun = get_sun(observation_time)
    separation = gcrs_target.separation(sun)
    position_angle = gcrs_target.position_angle(sun)

    if not math.radians(90) - Y_POINTING_THRESH <= separation.rad <= math.radians(90) + Y_POINTING_THRESH:
        raise ValueError('Sun-Target separation is not within nominal range. Must be between {} and {} radians,'
                         ' not {}'.format(
            round(math.radians(90) - Y_POINTING_THRESH, 5),
            round(math.radians(90) + Y_POINTING_THRESH, 5),
            round(separation.rad, 5)
        ))

    if roll_angle is not None:
        desired_pointing_y = ref_target.directional_offset_by(
            roll_angle, Angle(90, unit=u.deg)
        )

        separation = desired_pointing_y.transform_to(GCRS(obstime=observation_time)).separation(sun)

        if separation.rad > Y_POINTING_THRESH:
            raise ValueError('User selected roll angle violates pointing constraints. Sun/Y-axis separation must be'
                             ' less than {} deg, not {} deg'.format(
                round(np.rad2deg(Y_POINTING_THRESH), 5),
                round(separation.deg, 5)
            ))

        pay = roll_angle

    else:
        desired_pointing_y = gcrs_target.directional_offset_by(
            position_angle, Angle(90, unit=u.deg)
        ).transform_to(ref_frame)

        pay = position_angle

    # Create orthonormal basis
    zj_vector = Vector.from_radec(ref_target.ra.rad, ref_target.dec.rad).normalize()
    yj_vector = Vector.from_radec(desired_pointing_y.ra.rad, desired_pointing_y.dec.rad).normalize()
    ref_orthogonal_vector = yj_vector.cross(zj_vector)

    dot = yj_vector.dot(zj_vector)

    if abs(dot) > 1E-10:
        cross = yj_vector.cross(zj_vector)
        correction_q = Quaternion.from_axis_angle(cross, np.rad2deg(np.arccos(dot)) - 90)
        yj_vector = correction_q.rotate(yj_vector)
        ref_orthogonal_vector = yj_vector.cross(zj_vector)

    ref_basis = np.array([
        [ref_orthogonal_vector.x, yj_vector.x, zj_vector.x],
        [ref_orthogonal_vector.y, yj_vector.y, zj_vector.y],
        [ref_orthogonal_vector.z, yj_vector.z, zj_vector.z]
    ])

    q_array = Rotation.from_matrix(ref_basis).as_quat()
    desired_attitude_quaternion = Quaternion(*q_array)

    return desired_attitude_quaternion, pay


def calculate_target_position_and_y_axis(observation_time: Time, desired_att_quaternion: Quaternion,
                                         check_sun: bool = True, ref_frame: str = 'icrs') -> tuple:
    """
    Calculates the target position for a given desired attitude quaternion. The position angle of the
    spacecraft y-axis is also calculated.  Also, optionally, checks the separation between the y-axis
    and the sun against the threshold value.  If that fails, it also checks the separation between the
    target and the target threshold value.
    Args:dec
        observation_time (Time): Time of observation.
        desired_att_quaternion (Quaternion): The quaternion that transforms the spacecraft pointing (z) axis onto the
            J2000 target sky position.
        check_sun (bool): Flag to check if the y-axis is within pointing constraints of the sun.
        ref_frame (str): The reference frame of the target coordinates. This is also the frame that the output
        quaternion will transform spacecraft coordinates into.
    Returns:
        target_ra (float): The target Right Ascension in J2000 degrees.
        target_dec (float): The target Declination in J2000 degrees.
        y_ra (float): The y-axis pointing direction Right Ascension in J2000 degrees.
        y_dec (float): The y-axis pointing direction Declination in J2000 degrees.
        pa_y (float): Position angle of the spacecraft y-axis (solar panel pointing direction) relative to the
        target.
    """
    tval = Time(observation_time, format='isot', scale='utc')
    target_ra, target_dec = desired_att_quaternion.rotate(Vector(0, 0, 1)).to_radec()

    target_ra = Angle(target_ra, unit=u.rad)
    target_dec = Angle(target_dec, unit=u.rad)
    target = SkyCoord(ra=target_ra, dec=target_dec, frame=ref_frame)

    y_ra, y_dec = desired_att_quaternion.rotate(Vector(0, 1, 0)).to_radec()
    y_ra = Angle(y_ra, unit=u.rad)
    y_dec = Angle(y_dec, unit=u.rad)

    y_axis = SkyCoord(ra=y_ra, dec=y_dec, frame=ref_frame)
    gcrs_y_axis = y_axis.transform_to(GCRS(obstime=tval))

    sun = get_sun(tval)

    if check_sun:
        separation = gcrs_y_axis.separation(sun)

        if separation > THRESH_ANGLE:
            sep = target.separation(sun)
            if not SEP_MIN <= sep <= SEP_MAX:
                raise ValueError(
                    'Sun-Target separation {:.4f} is not within nominal range of {:.4f} - {:.4f} deg'.format(
                        sep.deg, SEP_MIN.deg, SEP_MAX.deg))
            else:
                raise ValueError('Sun-Y-axis separation {:.4f} is not within nominal range of <= {:.4f} deg.'.format(
                    separation.deg, THRESH_ANGLE
                ))

    y_pa = target.position_angle(y_axis)
    return target_ra.deg, target_dec.deg, y_ra.deg, y_dec.deg, y_pa.deg


def ixpecalcfov(args=None, **kwargs):
    """Calculates a map of the nominal sky field of view for each detector.
    
    ixpecalcfov is a stand-along mission planning tool that computes the
    nominal (non-dithered) field of view for a user-selectable sub-set of
    the three detectors, sky position (ra, dec) and observing time (time).
    The output is a FITS image file (user selectable with outfile) with 1âs
    indicating sky pixels within the field of view and 0âs indicating sky
    pixels outside the field of view. The user can customize the result by
    specifying a custom roll angle (roll) or position angle of the
    spacecraft Y-axis, the celestial reference frame (refframe), and the
    detectors included in the field of view image (selected by setting
    use_d1, use_d2, and use_d3, where setting the value to True will
    include the given detector in the field of view calculation).

    By default, the alignment quaternions, telescope definition data, and
    bad pixel lists are obtained from the IXPE CALDB. align is used to
    designate the name of a custom file of alignment quaternions; teldef is
    used to designate the name of a custom file of telescope definition
    data; and badpix1, badpix2, and badpix3 are used to designate the names
    of custom files for defining pixels of each corresponding detector to
    exclude from the field of view. The bad pixel files use flags that
    designate various types of bad pixels as well as âgrayâ pixels that may
    be optionally selected for exclusion by setting exc_graypix=True.
   
    Parameters:
    -----------
    time* (str)
          Observation date and time in ISOT format.

    ra* (float)
          Right ascension of target in degrees.

    dec* (float)
          Declination of target in degrees.

    outfile* (str)
          Path name of output FITS image file.

    roll (float)
          Position angle of the spacecraft y-axis. Default is the computed
          value, which orients the y-axis toward the sun at the
          observation date and time.

    refframe (str)
          Celestial reference frame of input position. (default: icrs)

    align (str)
          Path to the align CALDB file. (default: -).

    teldef (str)
          Path to the teldef CALDB file. (default: -).

    badpix1 (str)
          Path to the detector 1 bad pixel CALDB. (default: -)

    badpix2 (str)
          Path to the detector 2 bad pixel CALDB. (default: -)

    badpix3 (str)
          Path to the detector 3 bad pixel CALDB. (default: -)

    exc_graypix (bool)
          Exclude "gray" pixels from the field of view? (default: no)

    use_d1 (bool)
          Calculate detector 1 field of view? (default: yes)

    use_d2 (bool)
          Calculate detector 2 field of view? (default: yes)

    use_d3 (bool)
          Calculate detector 3 field of view? (default: yes)

    clobber
          Overwrite existing output file? (default: no)
          
    """
    calcfov_task = CalcFOVTask('ixpecalcfov')
    result = calcfov_task(args, **kwargs)
    return result
