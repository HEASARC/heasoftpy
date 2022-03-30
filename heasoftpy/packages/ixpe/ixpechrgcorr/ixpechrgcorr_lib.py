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

__description__ = \
    """Correct an input event list for the GEM charging.

This application is meant to process a run, build an energy-flux
cube (i.e., a three dimentional histogram containing the deadtime-corrected
energy flux as a function of DETX, DETY and TIME), numerically integrate the
charging model to calculate the evolution of the gain as a function of position
and time, and add a corrected PHA column in the photon list.

All the parameters of the charging model can be set via command-line switches.
"""

import sys
import os

from itertools import repeat
from operator import contains

import numpy

from astropy.io import fits
from datetime import datetime

import shutil

# we can use the logger of heasoftpy
# from .logging_ import logger, abort

from .utils import fixed_interval_time_binning, unix_to_string, met_to_unix
from .files import open_fits_file, fits_openfile, read_initial_charging_map, \
    read_charging_parameters, write_charging_map_to_file, NOT_AVLB

from .charging import EnergyFluxCube, FIDUCIAL_HALF_SIZE, \
    read_initial_charging_map, read_charging_parameters  # , \
#		     write_charging_map_to_file, NOT_AVLB


## heasoftpy-relevent part; make sure the new heasoft is in PYTHONPATH
from heasoftpy.core import HSPTask, HSPResult, HSPTaskException
from heasoftpy import fcn, utils
import logging

__appname__ = 'ixpechrgcorr'


class IXPEchrgcorrTask(HSPTask):
    """wrapper for ixpechrgcorr"""

    def exec_task(self):

        # put the parameters in to a list of par=value
        params = self.params

        # logger
        logger = self.logger

        # return code: 0 if task runs sucessful; set to 0 at the end
        returncode = 1

        ## ----------------- ##
        ##  start code here  ##
        ## ----------------- ##
        infile = params['infile']
        outfile = params['outfile']
        paramsfile = params['paramsfile']
        initmapfile = params['initmapfile']
        outchrgmapfile = params['outmapfile']
        timebinsize = params['timebinsize']
        phamin = params['phamin']
        phamax = params['phamax']
        phacol = params['phacol']
        poscol = params['poscol']
        clobVal = params['clobber']

        if clobVal in ['n', 'no', 'No', '0']:
            if os.path.isfile(outfile):
                raise HSPTaskException(f'The output file {outfile} already exists. Stop processing')

        # call main function of the task
        _ixpechrgcorr(infile, outfile, initmapfile, paramsfile,
                      outchrgmapfile, timebinsize, phamin, phamax, phacol, poscol)

        returncode = 0
        ## ----------------- ##
        ##  end code  ##
        ## ----------------- ##

        # get the captured output messages written to the logger
        outMsg, errMsg = self.logger.output

        return HSPResult(returncode, outMsg, errMsg, params)

    def task_docs(self):
        return ixpechrgcorr.__doc__


def ixpechrgcorr(args=None, **kwargs):
    """Appy the charging correction for IXPE event files
    
    'ixpechrgcorr' apply the charging correction to the PHA values of IXPE
    event files. The charging effect is due to the fact that, when the GPD
    is irradiated, part of the charge from the avalanche in the GEM can be
    temporarily deposited onto specific regions of the dielectric
    substrate, which in turns tend to modify the configuration of the
    electric field in the holes, potentially causing measurable changes in
    the gain.

    The rate-dependent gain variations due to the charging have been
    extensively characterized and calibrated and 'ixpechrgcorr' minimizes
    these effects. A key input of the 'ixpechrgcorr' is the initial
    charging map file in each spatial bin which describes the charge status
    of the detector at the beginning of the observation.

    For more details on the charging effect see Baldini et al. (2022),
    Astroparticle Physics, Volume 133.
    
    
    Parameters:
    -----------
    infile [file name]
          Name of the input FITS Event File.

    outfile [file name]
          Name of the output FITS Event File.

    (paramsfile=CALDB) [filename]
          Name of the charging parameters calibration file. If set to
          CALDB (default), use the file in the Calibration Database.

    initmapfile [file name]
          Name of the initial charging map file.

    (outmapfile=NONE) [file name]
          Name of the optional output charging map file. Set to NONE
          (default) for none.

    (timebinsize=30.0) [real]
          Size of temporal bin (seconds).

    (phamin=0.0) [real]
          Minimum PHA for the flux cube.

    (phamax=30000.0) [real]
          Maximum PHA for the flux cube.
          
    (phacol=PHA_T) [string]
          Name of the input PHA column.

    (poscol=ABS) [string]
          Base name of the input position columns.

    (clobber=no) [boolean]
          If set to yes, overwrite the output file.
          
    """
    task = IXPEchrgcorrTask('ixpechrgcorr')
    result = task(args, **kwargs)
    return result


def _ixpechrgcorr(input_file_paths, outFile,
                  initmapfile, params_file,
                  outchrgmapfile,
                  timebinsize,
                  minPha, maxPha,
                  phacol, poscol,
                  **kwargs):
    """Run the GEM charging correction.
    """

    logger = logging.getLogger('ixpechrgcorr')

    cmd1 = "ixpechrgcorr infile=" + input_file_paths
    cmd2 = " outfile=" + outFile + " paramsfile=" + params_file
    cmd3 = " initmapfile=" + initmapfile + " outchrgmapfile=" + str(outchrgmapfile)
    cmd4 = " timebinsize=" + str(timebinsize)
    cmd5 = " phamin=" + str(minPha) + " phamax=" + str(maxPha) + \
           " phacol=" + str(phacol) + " poscol=" + str(poscol)

    logger.info("")
    logger.info("--------------------------------------------------------------")
    logger.info(" \t %s Running ixpechrgcorr" % datetime.now())
    logger.info("--------------------------------------------------------------")
    logger.info("            Input Parameters List: ")
    logger.info("Name of the input ixpechrgcorr file  : %s" % input_file_paths)
    logger.info("Name of the output ixpechrgcorr file : %s" % outFile)
    logger.info("Name of Calibration file             : %s" % params_file)
    logger.info("Name of initmapfile calibration file : %s" % initmapfile)
    logger.info("Name of outchrgmapfile file          : %s" % outchrgmapfile)
    logger.info("timebinsize                          : %s" % str(timebinsize))
    logger.info("phamin                               : %s" % str(minPha))
    logger.info("phamax                               : %s" % str(maxPha))
    logger.info("phacol                               : %s" % str(phacol))
    logger.info("poscol                               : %s" % str(poscol))
    logger.info("--------------------------------------------------------------")

    shutil.copy(input_file_paths, outFile)

    # Open the input files and store them in a list
    # Note: reading files in astropy is done in a lazy way - i.e. the HDUs are
    # not immediately parsed when the file is read, so this should be fast
    hdu_lists = [open_fits_file(outFile, mode='update')]

    # Loop over the files once to get the overall time edges
    start_met, stop_met = None, None
    for hdu_list in hdu_lists:
        primary_header = hdu_list['PRIMARY'].header
        detnameInFile = primary_header['DETNAM']
        dateObs = primary_header['DATE-OBS']
        logger.info('Infile DETNAM = %s' % detnameInFile)
        logger.info('Infile DATE-OBS = %s' % dateObs)
        tstart = primary_header['TSTART']
        tstop = primary_header['TSTOP']
        if tstart > tstop:
            raise ValueError('Observation start time cannot be greater than '
                             'observation end time')
        if start_met is None or tstart < start_met:
            start_met = tstart
        if stop_met is None or tstop > stop_met:
            stop_met = tstop

    # get current Date&Time info
    lclDate = dateObs[:10]
    lclTime = dateObs[11:]

    if params_file == "CALDB":
        logger.info('Using CALDB as Calibration file')

        #        (filename, count) = quizcif2("IXPE", "GPD", "CHRGPARAMS", detnameInFile, lclDate, lclTime, exp='-', quality 0 )
        #        if count > 1:

        res = fcn.quzcif(mission='ixpe', instrument='gpd', detector=detnameInFile, filter='-', codename='CHRGPARAMS', \
                         date=lclDate, time=lclTime, expr='-', quality=0)

        #        logger.info("Item(s) found(s): %s - first file name: %s" %(((len(res.output))-1), (res.output[0])))
        tmp2 = (res.output[0]).split()
        #        logger.info("tmp2: %s" %tmp2[0])

        if tmp2[0] == 'ERROR':
            logger.info('No calibration files are found in CALDB. Stop processing')
            os.remove(outFile)
            sys.exit("No calibration files are found in CALDB. Stop processing")
        if (len(res.output)) > 2:
            logger.info('Found more than one file in CALDB matching the query. Stop processing')
            os.remove(outFile)
            sys.exit("Found more than one file in CALDB matching the query. Stop processing")
        elif (len(res.output)) == 1:
            logger.info('No calibration files are found in CALDB. Stop processing')
            os.remove(outFile)
            sys.exit("No calibration files are found in CALDB. Stop processing")
        else:
            tmp = (res.output[0]).split()
            filename = tmp[0]

            # open CALDB file
#            calDbExtension = open_fits_file(filename)['CHRG_PAR']
            calDbExtension = fits_openfile(filename)['CHRG_PAR']
            
            charging_parameters = calDbExtension.data[0]

    #	    params['KC_FAST'], params['TD_FAST'], params['DM_FAST'], \
    #           params['KC_SLOW'], params['TD_SLOW'], params['DM_SLOW']

    else:
        logger.info('Calibration file = %s' % params_file)
        charging_parameters = read_charging_parameters(params_file)

    # Read the map of the initial charging
    initial_dg_fast, initial_dg_slow, lclChargVal = \
        read_initial_charging_map(initmapfile)

    # The number of bins per detector side is determined by the initial charging
    # map
    nside = initial_dg_fast.shape[0]

    #    logger.debug('ixpechrgcorr detnameChargVal=%s' %lclChargVal)
    #    logger.debug('ixpechrgcorr detnameInFile=%s' %detnameInFile)

    if lclChargVal != detnameInFile:
        logger.info( \
            'Error Input event and initial charging map files have different values of keyword DETNAM')
        os.remove(outFile)
        sys.exit(0)

    # Check 'XPCHRG' key into "Events" section of input fits
    xpchrgKey = None
    xpchrgSts = 0
    for hdu_list in hdu_lists:
        events_header = hdu_list['EVENTS'].header
        try:
            xpchrgKey = events_header['XPCHRG']

            if xpchrgKey in [bool("T")]:
                logger.info('Found keyword XPCHRG=T in input file, the PHA_CHG column will be overwritten')
                #             print ("\nupdate XPCHRG key with comment set to new string Charging correction applied\n")
                xpchrgSts = 2  # key exist and value is "T"
            else:
                logger.info('Writing XPTCHRG key with value T')
                #             print ("\nupdate XPCHRG key value to T and comment set to Charging correction applied\n")
                xpchrgSts = 3  # key exist and value is "F"

        except:
            logger.info('XPCHRG key not found into input event file')
            xpchrgSts = 1  # key dosen't exist

        # set key to "T"
        events_header.set('XPCHRG', bool('T'),
                          comment="Charging correction applied",
                          after="ZSUPTHR")

        # add History
        now = datetime.now()
        dt_txt = now.strftime("%Y-%m-%dT%H:%M:%S ")

        cmd0 = "ixpechrgorr: " + dt_txt
        events_header.add_history(cmd0)
        cmdFull = cmd1 + cmd2 + cmd3 + cmd4 + cmd5

        events_header.add_history(cmdFull)

    # Create the EnergyFluxCube object
    tedges = fixed_interval_time_binning(start_met, stop_met, timebinsize)
    cube = EnergyFluxCube(nside, tedges)
    # Create an array to store the total livetime in each time slice. This will
    # be used to normalize the energy flux cube for the dead time.
    livetime_vs_time = numpy.zeros(len(tedges) - 1)
    # Loop over the files again, read the relevant columns and fill the cube.
    # We store the selection masks for later use
    logger.info('Filling the energy flux cube...')
    masks = []
    for i, hdu_list in enumerate(hdu_lists):
        data = hdu_list['EVENTS'].data
        num_clu = data['NUM_CLU']
        pha = data[phacol]
        livetime = data['LIVETIME']
        time_ = data['TIME']
        detx = data['%sX' % poscol]
        dety = data['%sY' % poscol]
        noise_mask = (num_clu > 0)
        fiducial_mask = (numpy.abs(detx) < FIDUCIAL_HALF_SIZE) * \
                        (numpy.abs(dety) < FIDUCIAL_HALF_SIZE)
        time_mask = (livetime >= 0) * (time_ >= start_met) * (time_ <= stop_met)
        mask = noise_mask * fiducial_mask * time_mask
        masks.append(mask)
        #        logger.info('%d events selected from %s.' % \
        #                    (mask.sum(), input_file_paths[i]))
        logger.info('%d events selected from %s.' % \
                    (mask.sum(), input_file_paths))
        # Fill the cube and calculate the gain profile.
        cube.fill(detx[mask], dety[mask], time_[mask], pha[mask])
        # Fill the livetime array. Livetime is in microseconds, so we convert
        # it to seconds before filling. We also discard the first event,
        # which is affected by a known bug in the livetime.
        # Note that we do not apply the noise and fiducial masks here, as that
        # would bias the dead time estimate.
        livetime_vs_time_, _ = numpy.histogram(time_[time_mask][1:],
                                               weights=livetime[time_mask][1:] / 1.e6, bins=tedges)
        livetime_vs_time += livetime_vs_time_
    # Normalize the energy flux cube
    logger.info('Done.')
    logger.info('Normalizing for the pixel area and the dead time...')
    cube.normalize(livetime=livetime_vs_time)
    logger.info('Done.')
    logger.info('Integrating the charging model...')
    cube._calculate_gain_data(initial_dg_fast, initial_dg_slow,
                              *charging_parameters)

    logger.info('Done.')

    #    if outchrgmapfile is not NONE:
    if outchrgmapfile != 'NONE':
        detnam = primary_header.get('DETNAM', NOT_AVLB)
        det_id = primary_header.get('DET_ID', NOT_AVLB)
        start_date = unix_to_string(met_to_unix(stop_met), fmt="%m/%d/%Y")
        start_time = unix_to_string(met_to_unix(stop_met), fmt="%H:%M:%S")
        write_charging_map_to_file(outchrgmapfile, cube.final_fast_map,
                                   cube.final_slow_map, start_time=start_time,
                                   start_date=start_date,
                                   detnam=detnam, det_id=det_id,
                                   version=1, creator=__appname__)

    logger.info('Applying the gain correction to input files...')
    for (input_file_path, hdu_list, mask) in zip(
            input_file_paths, hdu_lists, masks):
        data = hdu_list['EVENTS'].data
        time_ = data['TIME']
        detx = data['%sX' % poscol]
        dety = data['%sY' % poscol]
        pha = data[phacol]
        gain = cube.gain(detx[mask], dety[mask], time_[mask])

        # Correct the pha for the gain drift.
        corr_pha = numpy.copy(pha)
        corr_pha[mask] = pha[mask] / gain
        logger.info('Done.')

        # Write the corrected PHA column and write the output file.

        #
        #        if xpchrgSts==2:
        #        # col 'PHA_CHG' already exist
        #             data['PHA_CHG'] = corr_pha
        #        else:
        #            hdu_list['EVENTS'].data = append_fields(data, 'PHA_CHG', corr_pha,
        #                                                usemask=False)
        #        logger.info('Writing to file %s...' % outFile)
        #        hdu_list.writeto(outFile, overwrite=True)

        if xpchrgSts == 2:
            # col 'PHA_CHG' already exist
            data['PHA_CHG'] = corr_pha
        else:
            orig_cols = data.columns
            new_col = fits.ColDefs([
                fits.Column(name='PHA_CHG', format='1E', array=corr_pha)])

            new_hdu = fits.BinTableHDU.from_columns(orig_cols + new_col,
                                                    header=hdu_list['EVENTS'].header)
            hdu_list['EVENTS'] = new_hdu

            logger.info('Writing to file %s...' % outFile)
            hdu_list.flush()

    logger.info('Done.')
