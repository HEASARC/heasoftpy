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
import shutil

import numpy as np
from typing import List, TextIO
from heasoftpy.fcn.fselect import fselect

from astropy import units
from astropy.coordinates import Angle
from astropy.table import Table
from astropy.io import fits
import logging

from heasoftpy.core import HSPTask, HSPResult
from ..versioning import VERSION

TEMP_DIR = os.path.join(os.getcwd(), 'tmp')
TEMP_FILE = "tmp.fits"
TEMP_PATH = os.path.join(TEMP_DIR, TEMP_FILE)

P_MAX_SCALED = 50  # length of reference vector in pixels

SUPPORTED_COORD_SYS = [
    'image',
    'linear',
    'fk4',
    'b1950',
    'fk5',
    'j2000',
    'galactic',
    'ecliptic',
    'icrs',
    'physical',
    'wcs'
]

SUPPORTED_REGION_SHAPES = [
    'circle',
    'ellipse',
    'box',
    'line',
    'polygon',
    'point',
    'annulus'
]


class PolarizationTask(HSPTask):

    name = 'ixpepolarization'

    def exec_task(self):
        infile = self.params['infile']
        region_file = self.params['regfile']
        t_lo = self.params['t_lo']
        t_up = self.params['t_up']
        pi_lo = self.params['pi_lo']
        pi_up = self.params['pi_up']
        color = self.params['color']
        outfile = self.params['outfile']
        scale = self.params['scale']

        logger = logging.getLogger(self.name)

        if not os.path.exists(infile):
            err_str = 'Cannot find input events file: {}'.format(infile)
            logger.error(err_str)
            raise ValueError(err_str)

        if region_file != '-' and not os.path.exists(region_file):
            err_str = 'Cannot find input region file: {}'.format(region_file)
            logger.error(err_str)
            raise ValueError(err_str)

        t = Table.read(infile, hdu='EVENTS')
        os.makedirs(TEMP_DIR, exist_ok=True)

        if region_file == '-':
            regions = ['-']
        else:
            regions = create_component_region_files(region_file)

        if not regions:
            err_str = f'No valid regions found in input region file. Supported regions: \n {SUPPORTED_REGION_SHAPES}'
            logger.error(err_str)
            raise ValueError(err_str)

        if outfile == '-':
            outfile = f'{os.path.basename(infile).split(".")[0]}_{os.path.basename(region_file).split(".")[0]}_pol.reg' \
                if region_file != '-' else f'{os.path.basename(infile).split(".")[0]}_pol.reg'

        if color == '-':
            color = 'green'

        if scale == '-':
            scale = 0.1
        else:
            scale = float(scale)

        header = fits.getheader(infile, extname='EVENTS')
        x_index = t.colnames.index('X') + 1
        y_index = t.colnames.index('Y') + 1
        x_crpx = header['TCRPX{}'.format(x_index)]
        x_crvl = header['TCRVL{}'.format(x_index)]
        x_delt = header['TCDLT{}'.format(x_index)]
        y_crpx = header['TCRPX{}'.format(y_index)]
        y_crvl = header['TCRVL{}'.format(y_index)]
        y_delt = header['TCDLT{}'.format(y_index)]

        region_lines = []
        for region in regions:
            expr = ''
            if t_lo != '-':
                expr += f'TIME >= {t_lo} && '

            if t_up != '-':
                expr += f'TIME <= {t_up} && '

            if pi_lo != '-':
                expr += f'PI >= {pi_lo} && '

            if pi_up != '-':
                expr += f'PI <= {pi_up} && '

            if region != '-':
                expr += f"regfilter('{region}')"

            if expr.endswith(' && '):
                expr = expr[:-4]

            if expr == '':
                t = Table.read(infile, hdu='EVENTS')

            else:
                # Remove events based on PI, TIME, and specified region
                fselect(
                    infile=infile,
                    outfile=TEMP_PATH,
                    expr=expr,
                    clobber='yes',
                    copyall='no'
                )

                t = Table.read(TEMP_PATH, hdu='EVENTS')

            if len(t) == 0:
                if region != '-':
                    with open(region, 'r') as f:
                        err_str = 'No events found meet the specified criteria in region: \n {}'.format(f.readlines())
                        logger.error(err_str)
                        raise ValueError(err_str)
                else:
                    err_str = 'No events meet the specified criteria'
                    logger.error(err_str)
                    raise ValueError(err_str)

            x_max = np.ceil(np.max(t['X']))
            x_min = np.floor(np.min(t['X']))
            y_max = np.ceil(np.max(t['Y']))
            y_min = np.floor(np.min(t['Y']))

            x_mid = (x_max + x_min) / 2
            y_mid = (y_max + y_min) / 2

            q = 0
            u = 0
            w_mom = 0
            for row in t:
                q += row['Q'] * row['W_MOM']
                u += row['U'] * row['W_MOM']
                w_mom += row['W_MOM']

            q /= w_mom
            u /= w_mom
            p = np.sqrt(np.square(q) + np.square(u))

            rot_angle = -0.5 * np.arctan2(u, q)  # Psi is calculated as the angle from the detector x-axis

            ps = p * scale

            center_dec_reg = y_crvl + ((y_mid - y_crpx) * y_delt)
            center_ra_reg = x_crvl + (((x_mid - x_crpx) * x_delt) / np.cos(np.deg2rad(center_dec_reg)))

            ra_hms1 = Angle(center_ra_reg + ((ps / 2) * np.cos(rot_angle)), unit=units.deg).hms
            dec_dms1 = Angle(center_dec_reg + ((ps / 2) * np.sin(rot_angle)), unit=units.deg).dms

            ra_hms2 = Angle(center_ra_reg - ((ps / 2) * np.cos(rot_angle)), unit=units.deg).hms
            dec_dms2 = Angle(center_dec_reg - ((ps / 2) * np.sin(rot_angle)), unit=units.deg).dms

            region_lines.append(
                'icrs;line('
                '{}:{:02}:{:02},'
                '{:+02}:{:02}:{:02},'
                '{}:{:02}:{:02},'
                '{:+02}:{:02}:{:02}'
                ') # color={}\n'.format(
                    int(ra_hms1.h), int(ra_hms1.m), ra_hms1.s,
                    int(dec_dms1.d), int(dec_dms1.m), dec_dms1.s,
                    int(ra_hms2.h), int(ra_hms2.m), ra_hms2.s,
                    int(dec_dms2.d), int(dec_dms2.m), dec_dms2.s,
                    color
                ))

        if region_file != '-':
            with open(region_file, 'r') as fi:
                with open(outfile, 'w+') as fo:
                    for line in fi.readlines():
                        fo.write(line)

                    for line in region_lines:
                        fo.write(line)
                    write_scaling_key(fo, abs(x_delt), scale, color)
                fi.close()
                fo.close()

        else:
            with open(outfile, 'w+') as fo:
                for line in region_lines:
                    fo.write(line)
                write_scaling_key(fo, abs(x_delt), scale, color)

        if os.path.exists(TEMP_DIR):
            shutil.rmtree(TEMP_DIR)

        logger.info(f'Output file written to {outfile}')

        outMsg, errMsg = self.logger.output
        return HSPResult(0, outMsg, errMsg, self.params)


def write_scaling_key(file: TextIO, x_delt: float, scale: float, color: str = 'green') -> None:
    """
    Creates the scaling key in the output region file by creating a box, line, and text region.
    Args:
        file (str): Path to file for which the key will be written.
        x_delt (float): degrees / pixel conversion factor.
        scale (float): Amount by which to scale the output polarization vectors by.
        color (str): The color that will be used to create the key

    Returns:
        None
    """
    file.write(f'image; box(500, 500, 150, 50, 0) # color={color}\n')
    file.write(f'image; line(435, 500, {435 + P_MAX_SCALED}, 500) # color={color}\n')
    file.write('image; text(535, 500) # color={} text={}'.format(color,
                                                                 '{' + 'P=' + str(round(P_MAX_SCALED / scale * x_delt,
                                                                                        6)) + '}\n'))


def create_component_region_files(original_file: str) -> List[str]:
    """
    Parses the input region file for all of its constituent regions. Creates a new region file containing each region
    and returns the paths to these files.
    Args:
        original_file (str): Path to the original region file

    Returns:
        filepaths (list): List of the paths to each component region file
    """
    os.makedirs(TEMP_DIR, exist_ok=True)
    with open(original_file, 'r') as of:
        components = []
        header = []
        regions = []

        coord_system = 'physical'  # physical is the default coordinate system by convention
        for line in of.readlines():
            components += line.split(';')
        for component in components:
            # TODO: Add support for mosaic tiles
            if component.lower().startswith(('#', 'global')):
                header.append(component)
            elif component.strip('\n').lower() in SUPPORTED_COORD_SYS:
                coord_system = component.strip('\n')
            elif any([component.strip(' ').lower().startswith(region) for region in SUPPORTED_REGION_SHAPES]):
                regions.append((coord_system, component))

        filepaths = []
        for i, region in enumerate(regions):
            path = os.path.join(TEMP_DIR, f'region_{i}.reg')
            with open(path, 'w+') as f:
                f.writelines(header)
                f.write(f'{region[0]};{region[1]}')
                f.close()
            filepaths.append(path)

    return filepaths


def ixpepolarization(args=None, **kwargs):
    """Calculates overall Stokes parameters for a user-defined region.
    
    ixpepolarization computes the overall Stokes parameters Q and U for a
    sky region defined by the user (e.g., using the display program ds9)
    over a user-defined time interval and a user-defined PI energy range.
    The program also outputs a display region file with the polarization
    fraction and orientation on the sky computed from the Q and U, as well
    as the standard error of the resulting Q and U values for the region.

    The tool requires an input IXPE event FITS file (infile) and optional
    sky region (regfile), time interval (t_lo, t_up), and energy bounds
    (pi_lo, pi_up). The default is to compute the Stokes parameters from
    all events in the file. Clearly, as IXPE is an imaging polarimeter,
    only Stokes parameters for a region of the sky will be scientifically
    interesting.

    It is therefore highly recommended that a region file be provided to
    ixpepolarization. From the Stokes parameters Q and U, the polarization
    fraction and the position angle of the polarization vector are also
    computed with the vector length scaled by the parameter (scale). A
    modified region file is output which, when displayed in ds9, includes a
    vector in each of the original regions denoting the polarization
    fraction and orientation on the sky, as well as the standard error of
    the resulting Q and U values for the region, along with a scale in the
    top right corner.
    
    
    Parameters:
    -----------
    
    infile* (str)
          Input FITS EVENTS file.

    regfile (str)
          Path to ASCII region definition file. (default: -)

    t_lo (str)
          ISOT date/time of lower time bound. (default: -)

    t_up (str)
          ISOT date/time of upper time bound. (default: -)

    pi_lo (str)
          Lower PI bound for event filtering. (default: -)

    pi_lo (str)
          Upper PI bound for event filtering. (default: -)

    color (str)
          Polarization vector display color. (default: red)

    scale (float)
          Polarization vector length scale factor. (default: 0.1)
          
    outfile (str)
          Path to output file. (default: is none)
    
    """
    polarization_task = PolarizationTask('ixpepolarization')
    result = polarization_task(args, **kwargs)
    return result
