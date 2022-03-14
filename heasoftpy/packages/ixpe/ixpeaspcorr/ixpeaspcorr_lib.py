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


import numpy as np
from typing import Tuple
from astropy.io import fits
from scipy import optimize
from scipy.interpolate import interp1d

from ..fits.factory import update_comments
from ..ixpeexpmap.ixpeexpmap_lib import GenericPixelMap, DETECTOR_WIDTH, DETECTOR_HEIGHT
from ..time import Time
from heasoftpy.fcn.quzcif import quzcif
from ..event_flags import Status2
import logging

from heasoftpy.core import HSPTask, HSPResult
from ..versioning import VERSION


class AspcorrTask(HSPTask):

    name = 'ixpeaspcorr'

    def exec_task(self):
        infile = self.params['infile']
        n = self.params['n']
        att_path = self.params['att_path']
        x_pix_mean = self.params['x_pix_mean']
        y_pix_mean = self.params['y_pix_mean']
        statout = self.params['statout'] in ['y', 'yes', True]
        keep_uncorr = self.params['uncorr'] in ['y', 'yes', True]

        logger = logging.getLogger(self.name)

        if n == '-':
            n = 300
        else:
            n = int(n)

        if att_path == '':
            att_path = None

        f = fits.open(infile, mode='update')
        events = f['EVENTS']
        evt_orig = events.data

        if 'XPASPCOR' in events.header.keys() and events.header['XPASPCOR']:
            err_str = 'XPASPCOR header card indicates the events in this file have already been corrected.'
            raise ValueError(err_str)

        # Filter out events with STATUS and STATUS2 flags set.
        status = np.array([not np.any(evt_orig['STATUS'][i])
                           and not (evt_orig['STATUS2'][i][Status2.NO_OBSERVE.value] or
                                    evt_orig['STATUS2'][i][Status2.NO_ASPECT_SOLUTION.value] or
                                    evt_orig['STATUS2'][i][Status2.BADPIXEL_EDGE.value] or
                                    evt_orig['STATUS2'][i][Status2.BADPIXEL_ANOMALY.value] or
                                    evt_orig['STATUS2'][i][Status2.GEO_SAA.value] or
                                    evt_orig['STATUS2'][i][Status2.NO_POINTING.value]) for i in range(len(evt_orig))])
        evt = evt_orig[np.where(status)]

        # Calculate the new coordinates and statistics
        coord_out, interp, stats_in, stats_out = compute_gaussian_stats(evt['TIME'], evt['X'], evt['Y'], float(n),
                                                                        x_pix_mean, y_pix_mean)
        # Calculate the full corrected data.
        x_corr = np.copy(evt_orig['X'])
        x_corr[status] = coord_out[0]
        y_corr = np.copy(evt_orig['Y'])
        y_corr[status] = coord_out[1]

        # Set the event data.
        cols = []
        for column in events.columns:
            if column.name in ['PIX_PHAS', 'PIX_PHAS_EQ']:
                cols.append(fits.Column(name=column.name, format='QI()', array=np.array(events.data[column.name],
                                                                                        dtype=np.object_),
                                        unit=column.unit))
            elif column.name not in ['X', 'Y']:
                cols.append(fits.Column(name=column.name, format=column.format, array=events.data[column.name],
                                        unit=column.unit, disp=column.disp, bzero=column.bzero, bscale=column.bscale))

        cols.insert(events.columns.names.index('X'), fits.Column(name='X', format=evt_orig.columns['X'].format,
                                                                 array=x_corr, unit='pixel'))
        cols.insert(events.columns.names.index('Y'), fits.Column(name='Y', format=evt_orig.columns['Y'].format,
                                                                 array=y_corr, unit='pixel'))

        # Get the uncorrected stats.
        # TODO: New stats would involve re-running the fitting routine again.  Is that worth it?
        if keep_uncorr:
            cols.append(fits.Column(name='X_UNCORR', format=evt_orig.columns['X'].format,
                                    array=events.data['X'], unit='pixel'))
            cols.append(fits.Column(name='Y_UNCORR', format=evt_orig.columns['Y'].format,
                                    array=events.data['Y'], unit='pixel'))

        # Calculate the original statistics.
        if statout and keep_uncorr:
            x_mean = np.array([np.nan for row in evt_orig])
            x_mean[status] = interp[0](evt['TIME'])
            y_mean = np.array([np.nan for row in evt_orig])
            y_mean[status] = interp[1](evt['TIME'])
            x_stddef = np.array([np.nan for row in evt_orig])
            x_stddef[status] = interp[2](evt['TIME'])
            y_stddef = np.array([np.nan for row in evt_orig])
            y_stddef[status] = interp[3](evt['TIME'])
            cols.append(fits.Column(name='X_AVG_UNCORR', format='D', array=x_mean, unit='pixel'))
            cols.append(fits.Column(name='X_STD_UNCORR', format='D', array=x_stddef, unit='pixel'))
            cols.append(fits.Column(name='Y_AVG_UNCORR', format='D', array=y_mean, unit='pixel'))
            cols.append(fits.Column(name='Y_STD_UNCORR', format='D', array=y_stddef, unit='pixel'))

        b = fits.BinTableHDU.from_columns(fits.ColDefs(cols), header=events.header)
        b.header['EXTNAME'] = 'EVENTS'
        b.header['XPASPCOR'] = (True, 'Aspect correction applied to image')
        b.header = update_comments(b.header)

        f['EVENTS'] = b
        f.close()

        if att_path is not None:
            obs_time = Time(f['EVENTS'].data['TIME'][0], format='ixpesecs')
            tf = obs_time.strftime('%Y-%m-%d_%H:%M:%S')
            yymmdd = tf.split('_')[0]
            hhmmss = tf.split('_')[1]

            teldef = quzcif(mission='ixpe', instrument='xrt', codename='teldef', detector='-', filter='-',
                            date=yymmdd, time=hhmmss, expr='-').stdout.split(' ')[0]
            if teldef == '':
                f.close()
                err_str = 'No telescope definition CALDB file could be found for the input observation time.'
                logger.error(err_str)
                raise LookupError(err_str)
            teldef = fits.getheader(teldef, extname='Primary')

            gpm = GenericPixelMap(
                DETECTOR_WIDTH,
                DETECTOR_HEIGHT,
                teldef['DET_XSCL'],
                teldef['DET_YSCL'],
                teldef['SKY_XSCL'],
                teldef['SKY_YSCL']
            )

            att_file = fits.open(att_path, mode='update')
            mask = np.greater(att_file['HK'].data['TIME'][1:], evt['TIME'][0])
            mask1 = np.less(att_file['HK'].data['TIME'][1:], evt['TIME'][-1])
            maskt = np.where(mask & mask1)
            txydz = att_file['HK'].data['TXYDZ']

            # Positive offsets on the sky are to the left so use -x
            txydz_pix = np.transpose([
                gpm._index_to_pixel(*gpm.skyfield_to_index(-np.rad2deg(row[0]), np.rad2deg(row[1])))
                for row in txydz
            ])
            xs = apply_interp_correction(att_file['HK'].data['TIME'][1:][maskt], np.array(txydz_pix[0][1:])[maskt],
                                         interp[0], stats_out[1] if x_pix_mean == '-' else float(
                    x_pix_mean))
            ys = apply_interp_correction(att_file['HK'].data['TIME'][1:][maskt], np.array(txydz_pix[1][1:])[maskt],
                                         interp[1], stats_out[2] if y_pix_mean == '-' else float(
                    y_pix_mean))
            txydz_corr = np.array([(np.nan, np.nan) for row in att_file['HK'].data])
            txydz_corr[1:][maskt] = [(round(x), round(ys[i])) for i, x in enumerate(xs)]
            att_cols = []
            for column in att_file['HK'].columns:
                if column.name == 'TXYDZ_CORR':
                    continue
                att_cols.append(
                    fits.Column(name=column.name, format=column.format, array=att_file['HK'].data[column.name],
                                unit=column.unit, disp=column.disp, bzero=column.bzero, bscale=column.bscale))
            att_cols.append(fits.Column(name='TXYDZ_CORR', format='2D', array=txydz_corr, unit='pixel'))
            b = fits.BinTableHDU.from_columns(fits.ColDefs(att_cols), header=fits.getheader(att_path, extname='HK'))
            att_file['HK'] = b
            att_file.close()

        f.close()

        outMsg, errMsg = self.logger.output
        return HSPResult(0, outMsg, errMsg, self.params)


def gaussian(height: float, center_x: float, center_y: float, width_x: float, width_y: float):
    """
    Creates and returns a 2-D gaussian lambda function based on the given parameters
    Params:
        height:  Estimated starting height of gaussian.
        center_x: Estimated starting center X-coordinate.
        center_y: Estimated starting center Y-coordinate.
        width_x:  Estimated stddev in X-axis.
        width_y:  Estimated stddev in Y-axis.
    """
    width_x = float(width_x)
    width_y = float(width_y)
    return lambda x, y: height * np.exp(
        -(((center_x - x) / width_x) ** 2 + ((center_y - y) / width_y) ** 2) / 2)


def moments(xdata: np.ndarray, ydata: np.ndarray):
    """
    Returns the height, x, y, width_x, width_y of a range of x and y data calculated
        from the simple mean and std. deviation in each axis.
    Params:
        xdata:  X-axis coordinates for sample.
        ydata:  Y-axis coordinates for sample.
    Returns:
        Numpy array of values:  height, x-mean, y-mean, x stddev, y stddev.
    """
    x = np.nanmean(xdata)
    y = np.nanmean(ydata)
    width_x = np.sqrt(np.nanmean(np.square(xdata)) - x * x)
    width_y = np.sqrt(np.nanmean(np.square(ydata)) - y * y)
    height = 1
    return np.array([height, x, y, width_x, width_y])


def error_function(fparam, data):
    """
    Computes the differences between a gaussian function computed from the input parameters
        and the data being modeled (calls the function "gaussian" from above).
    Params:
        fparam: The parameters in array form (height, x-center, y-center, x-width, y-width)
        data: The 2-d image array.
    Returns:
        Returns the output model - data values as a flat array.
    """
    height, center_x, center_y, width_x, width_y = fparam[0], fparam[1], fparam[2], fparam[3], fparam[4]
    return np.ravel(gaussian(height, center_x, center_y, width_x, width_y)(*np.indices(data.shape)) - data)


def fitgaussian(data: np.ndarray, fparams: np.ndarray):
    """
    Calculates the least-squares optimized 2-D gaussian using a set of starting parameter,
        the "error_function" function above, and the two-dimensional image data being fit.
    Params:
        data: The 2-D image data array.
        fparams:  The starting parameters (height, x-center, y-center, x-width, y-width) in array form.
    """
    return optimize.leastsq(error_function, fparams, (data,))


def calc_gauss_fit(xdata: np.ndarray, ydata: np.ndarray) -> Tuple[float, float, float, float, float]:
    """
    Calculates the 2-d Gaussian peak fit for a set of x, y values.  Assumes the values
        are floating point pixels in the IXPE sky plane (i.e. are in range 0-599 on each axis).
        The algorithm is:  (1) To use the moments function to calculate the center and width of
        the data arrays in several steps, using a smaller box around the center at each step.  (2)
        For the smallest box, convert the data to a 2-D array and then use the 2-D least-squares
        Gaussian fit to find the center and width in each dimension.
    Params:
        xdata:  The x-coordinate values of the points being analyzed.
        ydata:  The y-coordinate values of the points being analyzed.
    Returns:
        A tuple with the fitted height, x-center, y-center, x-stddev, and y-stddev values.
    """
    # Gaussian fit has five parameters, so we need more than 5 data points.
    M = 5

    # Create the number of steps, as well as the starting bounds for the boxes used
    #   to calculate the moments.
    m = [300, 150, 75, 37, 18, 10]
    dmin = 0
    dmax = 599
    cx = 300
    cy = 300
    xdat = np.copy(xdata)
    ydat = np.copy(ydata)
    outval = np.array([1., 300., 300., 100., 100.])

    # Loop over the half-widths for the moments calculation boxes.
    for im in m:
        # Calculate the dimensions of image box.
        x1 = max([int(cx) - im, dmin])
        x2 = min([int(cx) + im, dmax])
        y1 = max([int(cy) - im, dmin])
        y2 = min([int(cy) + im, dmax])

        # Find the x, y points within the box.
        xdat1 = []
        ydat1 = []
        for i in range(len(xdat)):
            if x1 < xdat[i] < x2 and y1 < ydat[i] < y2:
                xdat1.append(xdat[i])
                ydat1.append(ydat[i])

        # Calculate the centroid parameters using the moments of the box.
        newval = moments(np.array(xdat1), np.array(ydat1))

        # If any of the parameters in this round are nan, return the previous set
        #  of parameters.
        if np.any(np.isnan(newval)):
            return outval[0], outval[1], outval[2], outval[3], outval[4]

        # Set the parameters and the new box centers.  Boxes should always fall within
        #   the previous box, so reduce the size of the data set.
        outval = newval
        cx = outval[1]
        cy = outval[2]
        xdat = np.array(xdat1)
        ydat = np.array(ydat1)

    # Find the statistics.  If there are enough values, use the Gaussian.  Otherwise, use moments.
    if len(xdata) > M:
        skyim, xedge, yedge = np.histogram2d(xdat, ydat, range=[[x1, x2], [y1, y2]],
                                             bins=[x2 - x1 + 1, y2 - y1 + 1])
        skyim = skyim.T
        outval, num = fitgaussian(skyim, outval)

    return outval[0], outval[1], outval[2], outval[3], outval[4]


def compute_gaussian_stats(etime: np.ndarray, xarr: np.ndarray, yarr: np.ndarray, tlen: float = 300.,
                           x_mean: str = '-', y_mean: str = '-'):
    """
    Loops through the data, computing 2-D gaussian statistics for each tlen chunk of time.
    :param etime: Array of time values for the events.
    :param xarr: Array of sky x-positions for the events.
    :param yarr: Array of sky y-positions for the events.
    :param tlen: Length of time to integrate each gaussian (seconds. Default=300)
    :return:
    """
    tend = etime[-1]
    tval = []
    x_cen = []
    y_cen = []
    x_width = []
    y_width = []
    ipos = 0
    tstop = etime[0]
    while tstop < tend:
        # Get start and stop time from position and tlen, find first occurrence of time
        #   greater than tstop.
        tstart = etime[ipos]
        tstop = min([tstart + tlen, tend])
        ctime = (tstart + tstop) / 2
        jpos = np.argmax(etime[ipos:] >= tstop)

        # Nothing to worry about if jpos < 1, no events to correct.
        if jpos < 1:
            continue
        jpos += ipos

        # Calculate the gaussian fit for the events in this period of time.
        h, xc, yc, xw, yw = calc_gauss_fit(xarr[ipos:jpos + 1], yarr[ipos:jpos + 1])

        # Set the initial stats values to the initial time value.
        if ipos == 0:
            tval.append(tstart)
            x_cen.append(xc)
            y_cen.append(yc)
            x_width.append(xw)
            y_width.append(yw)

        # Set the stats values.
        tval.append(ctime)
        x_cen.append(xc)
        y_cen.append(yc)
        x_width.append(xw)
        y_width.append(yw)

        # Set the final stats values to the final time value.
        if tstop == tend:
            tval.append(tend)
            x_cen.append(xc)
            y_cen.append(yc)
            x_width.append(xw)
            y_width.append(yw)

        # Set the starting index for the next interval.
        ipos = jpos

    # Create interpolations.
    x_centroid = interp1d(np.array(tval), np.array(x_cen), kind='linear')
    y_centroid = interp1d(np.array(tval), np.array(y_cen), kind='linear')
    x_stddev = interp1d(np.array(tval), np.array(x_width), kind='linear')
    y_stddev = interp1d(np.array(tval), np.array(y_width), kind='linear')

    # Get overall centers.
    hmean, xmean, ymean, xmean_width, ymean_width = calc_gauss_fit(xarr, yarr)

    xmean = xmean if x_mean == '-' else float(x_mean)
    ymean = ymean if y_mean == '-' else float(y_mean)

    # Correct the events.
    x_corr = apply_interp_correction(etime, xarr, x_centroid, xmean)
    y_corr = apply_interp_correction(etime, yarr, y_centroid, ymean)

    # Return the stats and corrected events.
    hmean1, xmean1, ymean1, xmean_width1, ymean_width1 = calc_gauss_fit(x_corr, y_corr)

    # Bundle the return values.
    coord_out = [x_corr, y_corr]
    stats_in = [hmean, xmean, ymean, xmean_width, ymean_width]
    stats_out = [hmean1, xmean1, ymean1, xmean_width1, ymean_width1]
    interp = [x_centroid, y_centroid, x_stddev, y_stddev]

    return coord_out, interp, stats_in, stats_out


def apply_interp_correction(dtime: np.ndarray, data: np.ndarray, centroid, mean_position: float) -> np.array:
    """
    Subtracts the error from each event position. Error is calculated as the difference between the centroid of
    positions from the interpolated source.
    Args:
        dtime: Time of each event.
        data: X or Y position of each event.
        centroid: Interpolation function of computed centroids.
        mean_position: Computed mean for entire data set.

    Returns:
        corrected_positions (np.array): Contains each corrected position.
    """
    corrected_positions = np.empty_like(data)
    for i in range(len(dtime)):
        corrected_positions[i] = data[i] - (centroid(dtime[i]) - mean_position)

    return corrected_positions


def ixpeaspcorr(args=None, **kwargs):
    """Corrects for residual aspect errors using interpolated
    event position averages over time intervals of user-specified number of
    seconds.
    
    ixpeaspcorr uses event time stamps and sky X,Y values from an IXPE
    Level 1 event FITS file (infile) to compute average position over a
    time width of (n) seconds. A corrected position is then given for each
    event by subtracting the difference between the interplolated means of
    the n events and the mean of all events from the uncorrected position.
    If x_pix_mean and/or y_pix_mean are set to values other than â-â, these
    values will be used instead of the mean of all events.

    If statout=True, then the running mean and standard deviation for each
    axis position is added as columns X_AVG, X_STD, and Y_AVG, Y_STD. If
    uncorr=True, the original, uncorrected position columns are retained as
    X_UNCORR, Y_UNCORR and, if statout=True also, then the uncorrected
    statistics columns X_AVG_UNCORR, X_STD_UNCORR, Y_AVG_UNCORR, and
    Y_STD_UNCORR are also added. The input file is overwritten with these
    new columns added as well as a new keyword, XPASPCOR, to prevent
    unintentional multiple running of ixpeaspcorr.

    In addition, ixpeaspcorr will optionally calculate the interpolated
    position of the spacecraft ponting direction on the sky plan and add
    these values as a new column (TXYDZ_CORR) to an attitude file if
    att_path=True.
    
    Parameters:
    -----------
    infile* (str)
          Input FITS Event file

    n* (integer)
          Duration of time to group events in for fitting.

    statout (bool)
          Output standard deviation and mean of event positions? (default:
          no)

    uncorr (bool)
          Keep uncorrected positions in output file? If statout is also
          True, uncorrected stats will be output. (default: no)

    att_path (str)
          Attitude file to be corrected.

    x_pix_mean (float)
          Average x position (in pixels) of all detectors for observation.
          Default is the mean of the input detector only.

    y_pix_mean (float)
          Average y position (in pixels) of detectors for observation.
          Default is the mean of the input detector only.
          
    """
    aspcorr_task = AspcorrTask('ixpeaspcorr')
    result = aspcorr_task(args, **kwargs)
    return result
