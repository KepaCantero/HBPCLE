# ---LICENSE-BEGIN - DO NOT CHANGE OR MOVE THIS HEADER
# This file is part of the Neurorobotics Platform software
# Copyright (C) 2014,2015,2016,2017 Human Brain Project
# https://www.humanbrainproject.eu
#
# The Human Brain Project is a European Commission funded project
# in the frame of the Horizon2020 FET Flagship plan.
# http://ec.europa.eu/programmes/horizon2020/en/h2020-section/fet-flagships
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
# ---LICENSE-END
'''
Implementation of PyNNACSource
moduleauthor: probst@fzi.de
'''

from hbp_nrp_cle.brainsim.pynn.devices import PyNNPoissonSpikeGenerator
from hbp_nrp_cle.brainsim.pynn_nest.devices.__NestDeviceGroup import PyNNNestDevice, \
    create_transformation
import pyNN.nest as nestsim

__author__ = 'Georg Hinkel, Dimitri Probst'


class PyNNNestPoissonSpikeGenerator(PyNNNestDevice, PyNNPoissonSpikeGenerator):
    """
    Represents an alternating current generator.
    """

    transformations = {
        "rate": create_transformation("rate")
    }

    @property
    def rate(self):
        """
        Returns the frequency of the Poisson spike generator
        """
        return self._parameters["rate"]

    def sim(self):
        """
        Gets the simulator module to use
        """
        return nestsim

    # Pylint does not really recognize property overrides
    # pylint: disable=arguments-differ
    @rate.setter
    def rate(self, value):
        """
        Sets the amplitude of the current

        :param value: float
        """
        self._parameters["rate"] = value
        # The nest device is only available as protected property of the PyNN device
        # pylint: disable=protected-access
        self.SetStatus([self.device_id], {'rate': float(value)})

    @property
    def device_id(self):
        """
        Returns the internal device id
        """
        # pylint: disable=protected-access, no-member
        # PyNN creates a parrot neuron which is stored in the population
        # therefore, we have to subtract 1 to get the poisson generator
        return self._generator[0] - 1
