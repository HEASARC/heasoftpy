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
from scipy.interpolate import interp1d
import logging

from .utils import bisect_binning		#, open_fits_file

from .files import open_fits_file, read_initial_charging_map, \
                  read_charging_parameters, write_charging_map_to_file, NOT_AVLB


# Half side of the GPD active area [mm] minus 0.5~mm of padding
FIDUCIAL_HALF_SIZE = 7.


class ChargingModel:
    """ Class representing a double-component model for GEM charging. Each
    component is described by three parameters: the charging constant (k_c),
    the maximum fractional gain drop at full charging (delta_max) and the
    discharge time (tau_d). It is assumed that the two components contribute
    independently to the gain drop. They are called 'fast' and 'slow' because
    their charateristic times differ by roughly an order of magnitude.
    The model can be integrated on an arbitrary number of spatial dimensions -
    though the most useful case is that of a 2d map.

    Parameters
    ----------
    time_grid : array
        the times over which the model is integrated

    energy_flux : array
        the value of the input energy flux in the time bins defined by
        time_grid, in units of ADC counts/mm^2/s. The input energy flux can
        be a matrix of any shape but it is always assumed that the last axis is
        time, the others representing an arbitrary number of spatial dimensions.
    """
    def __init__(self, time_grid, energy_flux):
        """ Constructor.
        """
        # The time axis (that is the last dimension) of the energy flux grid
        # must match the number of bins defined by the input time grid
        assert energy_flux.shape[-1] == (len(time_grid) - 1)
        self.time_grid = time_grid
        self.energy_flux = energy_flux
        # Initialize the gain
        self.gain = numpy.full(self.shape(), 1.)
        # delta_g_fast and delta_g_slow have the same spatial dimensions
        # as the gain matrix
        self.delta_g_fast = numpy.full(self.shape()[:-1], 0.)
        self.delta_g_slow = numpy.full(self.shape()[:-1], 0.)

    def shape(self):
        """ The shape of the gain profile: spatial dimensions as
        self.energy_flux and time axis (the last one) as self.time_grid """
        return self.energy_flux.shape[:-1] + (self.time_grid.shape[0], )

    @staticmethod
    def step(flux, dt, dg, k_c, delta_max, tau_d):
        """ Compute a step of the charging model (for either the slow or fast
        process). For a description of the charging parameters see the
        integrate() method

        Parameters
        ----------
        flux: float or array
            the value of the input energy flux for this step (ADC counts/mm^2/s)

        dt : float
            the time step (in seconds)

        dg : float or array
            the current gain drop due to this process (fractional)
        """
        # Support a single component charging by returning immediately if
        # delta_max is 0
        if (delta_max == 0):
            return numpy.full(flux.shape, 0.)
        delta = flux * delta_max / k_c * (1. - dg / delta_max)
        if (tau_d != 0):
            delta -= (dg / tau_d)
        return delta * dt

    def integrate(self,
                  k_c_fast,
                  tau_d_fast,
                  delta_max_fast,
                  initial_dg_fast,
                  k_c_slow,
                  tau_d_slow,
                  delta_max_slow,
                  initial_dg_slow):

        """Calculate the expected space-time profile of the gain for a given
        illumination history. We are adopting a charging model with two
        components: one fast and one slow. Both are regulated by the same
        equation, which includes a rate-dependent charging and a constant
        discharging, with the caracteristic time for the two processes (fast
        and slow) separated by roughly an order of magnitude. The system is
        integrated using finite differences. The returned gain profile is
        computed on the times defined by self.time_grid and has the same
        spatial dimensions as the energy_flux attribute

        Parameters
        ----------
        k_c_fast : float
            the charging constant for the fast process (ADC counts/mm^2)

        tau_d_fast : float
            the discharge time constant for the fast process (seconds)

        delta_max_fast : float
            maximum fractional gain drop for the fast process

        initial_dg_fast : float or array
            initial fraction of gain drop due to the fast process. If an array,
            the value is given for each spatial bin - thus the dimension must
            match the spatial dimensions of self.energy_flux. If None, we
            assume initial full discharge for the fast component.

        k_c_slow : float
            as k_c_fast, but for the slow process

        tau_d_slow : float
            as tau_d_fast, but for the slow process

        delta_max_slow : float
            as delta_max_fast, but for the slow process

        initial_dg_slow : float
            as initial_dg_fast, but for the slow process
        """
        if initial_dg_fast is not None:
            self.delta_g_fast = initial_dg_fast * delta_max_fast
        if initial_dg_slow is not None:
            self.delta_g_slow = initial_dg_slow * delta_max_slow
        # Note: selecting the last axis no matter the rank with numpy '...'
        # syntax
        self.gain[..., 0] =  self.gain[..., 0] - self.delta_g_fast -\
                             self.delta_g_slow
        # In order to iterate over the last axis of the energy_flux tensor, we
        # take its transpose (by default numpy uses the first axis to iterate).
        # This has no effect for 1-d arrays
        for i, (dt, f) in enumerate(zip(numpy.diff(self.time_grid),
                                        self.energy_flux.T)):
            # Because of this 'trick' we have to take the transpose of the flux
            # 'f' here, for consistency (otherwise the other dimensions are
            # messed up).
            dg_fast = self.step(f.T, dt, self.delta_g_fast, k_c_fast,
                                delta_max_fast, tau_d_fast)
            dg_slow = self.step(f.T, dt, self.delta_g_slow, k_c_slow,
                                delta_max_slow, tau_d_slow)
            self.gain[..., i + 1] =  self.gain[..., i] - dg_fast - dg_slow
            # Update the fast an slow map with the current step
            self.delta_g_fast += dg_fast
            self.delta_g_slow += dg_slow
        # Now we express the final charging maps as a fraction of the
        # corresponding delta_max, to match the standard format
        if delta_max_fast > 0.:
            self.delta_g_fast /= delta_max_fast
        if delta_max_slow > 0.:
            self.delta_g_slow /= delta_max_slow
        return self.gain


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

    detnameChargVal = charging_map.header['DETNAM']
    logger.info('Charging File DETNAM = %s' % detnameChargVal)

    # Initialize the initial slow and fast values as 2d arrays filled with zeroes
    initial_dg_fast = numpy.full((nside, nside), 0.)
    initial_dg_slow = numpy.full((nside, nside), 0.)
    # We fill the two arrays without doing any assumption on the order of the
    # values in the FITS files, but using explicitly the index from the BINX
    # and BINY columns. This is slower but safer, as it will work even if we
    # change the ordering in the input file.
    logger.info('NUM_BINS = %d' % nside)
    fast = charging_map.data['FAST']
    slow = charging_map.data['SLOW']
    binx = charging_map.data['BINX']
    biny = charging_map.data['BINY']
    for i, (x, y) in enumerate(zip(binx, biny)):
        # Note: indexes of numpy are (row, column), so y goes first
        initial_dg_fast[y, x] = fast[i]
        initial_dg_slow[y, x] = slow[i]
    return initial_dg_fast, initial_dg_slow, detnameChargVal


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


class EnergyFluxCube(object):

    """Main data structure for the charging-induced gain correction. This is
    essentially a 3d histogram, which we fill with the counts in each time and
    space bin, weighting each event with its energy (in ADC counts). The bin
    weights are then normalized by the livetime and the bin area, so that the
    sum of weights in each bin is equal to the total energy flux
    received on that bin. This can be then used as input for calculating
    the charging correction.

    Parameters
    ----------
    nside : int
        the number of bins per side. The detector surface is divided in
        nside x nside bins

    tedges : array
        the time binning
    """
    def __init__(self, nside, tedges):
        """ Constructor.
        """
        self.edges = numpy.linspace(-FIDUCIAL_HALF_SIZE, FIDUCIAL_HALF_SIZE,
                                    nside + 1)
        self.tedges = numpy.copy(tedges)
        self.bin_edges = (self.edges, self.edges, self.tedges)
        self.shape = tuple(len(edge) - 1 for edge in self.bin_edges)
        self.bin_weights = numpy.zeros(shape=self.shape, dtype='d')
        self.num_entries = 0
        self.weights_sum = 0.
        # Cache the pixel area, which will be used later to normalize the flux.
        self.bin_area = (FIDUCIAL_HALF_SIZE * 2. / nside)**2.
        # Initialize the attribute that will store the estimated gain profile
        self._charging_model = None

    def xbinning(self):
        """Return the histogram binning on the detx axis.
        """
        return self.edges

    def ybinning(self):
        """Return the histogram binning on the dety axis.
        """
        return self.edges

    def tbinning(self):
        """Return the histogram binning on the time axis (aka z-axis).
        """
        return self.tedges

    def times(self):
        """Return the histogram binning on the time axis (aka z-axis).
        """
        return 0.5 * (self.tedges[1:] + self.tedges[:-1])

    @property
    def gain_data(self):
        """Return the estimated gain as a 3D matrix"""
        if self._charging_model is None:
            return None
        else:
            return self._charging_model.gain

    @property
    def final_fast_map(self):
        """ Map of the fast charging at the end of the integration"""
        if self._charging_model is None:
            return None
        else:
            return self._charging_model.delta_g_fast

    @property
    def final_slow_map(self):
        """ Map of the slow charging at the end of the integration"""
        if self._charging_model is None:
            return None
        else:
            return self._charging_model.delta_g_slow

    def fill(self, x, y, t, pha):
        """ Here we stack together all the sample vectors, transpose the
        array and use it as an argument to numpy.histogramdd(), using the pha
        as weight.

        Parameters
        ----------
        x : array
           the x of the event

        y : array
           the x of the event

        t : array
            the time of the event

        pha : array
           the energy of the event, used as a weight for each data entry
        """
        try:
            data = numpy.vstack((x, y, t)).T
        except Exception as e:
            shapes = (x.shape, y.shape, t.shape)
            logger.error('Cannot fill %s with sample shapes %s.' %\
                         (self.__class__.__name__, shapes))
            raise e
        assert len(pha) == data.shape[0]
        bin_weights, _ = numpy.histogramdd(data, bins=self.bin_edges,
                                           weights=pha)
        self.num_entries += data.shape[0]
        self.weights_sum += bin_weights.sum()
        self.bin_weights += bin_weights

    def normalize(self, livetime=None):
        """ Calculate the actual energy flux per unit area and
        overwrite the histogram content. Here we essentially take care of the
        energy weighting and the normalization by the elapsed time and the pixel
        area.

        Parameters
        ----------
        livetime : array
            the total livetime in each time bin. This is used to optionally
            correct the flux for the dead time
        """
        # We start by dividing the total energy in ech time and space bin by
        # the total livetime in the same time bin. If an array of livetimes
        # is provided, we use it, otherwise we assume that the dead time is
        # zerp - that is the livetime is simply the number of seconds in each
        # time slice.
        if livetime is not None:
            assert livetime.shape == self.times().shape
            # NOTE: numpy automatically broadcasts the 1d livetime array to
            # the shape of our 3d histogram before dividing.
            flux = self.bin_weights / livetime
            # Handle zero livetime bins - the flux there is zero by definition
            flux[numpy.isnan(flux) | numpy.isinf(flux)] = 0.
        else:
            flux = self.bin_weights / numpy.diff(self.tbinning())
        # Then, we normalize to the pixel area.
        flux /= self.bin_area
        # And, it goes without saying, update the histogram.
        self.bin_weights = flux

    def _calculate_gain_data(self,
                             initial_dg_fast,
                             initial_dg_slow,
                             k_c_fast,
                             tau_d_fast,
                             delta_max_fast,
                             k_c_slow,
                             tau_d_slow,
                             delta_max_slow):
        """Loop over the time history of the energy flux of the observation
        and calculate the expected gain space and time profile.

        The private ChargingModel istance attribute stores the gain data after
        integration. See that class for a description of the model
        parameters.
        """
        self._charging_model = ChargingModel(self.tbinning(), self.bin_weights)
        self._charging_model.integrate(
                          k_c_fast, tau_d_fast, delta_max_fast, initial_dg_fast,
                          k_c_slow, tau_d_slow, delta_max_slow, initial_dg_slow)

    def flux_trend(self):
        """ Return a time trend of the flux, integrated over the detector
        surface. """
        return self.bin_weights.sum(axis=(0, 1))

    def flux_map(self):
        """ Return a map of the flux integrated over time.
        """
        return self.bin_weights.sum(axis=2)

    def gain_trend(self, x, y):
        """ Return the trend of the gain in a given spatial bin.

        Parameters
        ----------
        x : int
            the requested column

        y : int
            the requested row
        """
        return self.gain_data[x, y]

    def gain(self, detx, dety, time_):
        """Return the expected corrected gain for a list of events at
        specific detector positions and times.

        Parameters
        ----------
        detx : float or numpy.array of float
            detector x coordinate(s) [mm] at which the gain has to bee evaluated

        dety : float or numpy.array of float
            detector y coordinate(s) [mm] at which the gain has to bee evaluated

        time_ : float or numpy.array of float
            time [MET] at which the gain has to bee evaluated
        """
        # If this is the first time the function is called, make sure to
        # integrate the charging model
        if self.gain_data is None:
            self._calculate_gain_data()
        # Find the correct bin of the gain histogram (a 3D matrix)
        i = bisect_binning(self.xbinning(), detx)
        j = bisect_binning(self.ybinning(), dety)
        # Here we specify the 'right' options to numpy.searchsorted to prevent
        # the first event from being assigned to the last time bin
        k = bisect_binning(self.tbinning(), time_, side='right')
        return self.gain_data[i, j, k + 1]
