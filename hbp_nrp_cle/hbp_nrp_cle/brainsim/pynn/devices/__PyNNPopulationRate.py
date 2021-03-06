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
Implementation of PyNNPopulationRate
moduleauthor: probst@fzi.de
'''

from hbp_nrp_cle.brainsim.common.devices import AbstractBrainDevice
from hbp_nrp_cle.brainsim.BrainInterface import IPopulationRate
# pylint: disable=no-name-in-module
from scipy.integrate import simps
import numpy as np

__author__ = 'Dimitri Probst, Sebastian Krach'


class PyNNPopulationRate(AbstractBrainDevice, IPopulationRate):
    """
    Represents the rate of a population of LIF neurons by
    measuring and normalizing the membrane potential of a
    leaky integrator with decaying-exponential post-synaptic currents
    """

    default_parameters = {
        'tau_fall': 20.0,
        'tau_rise': 10.0
    }

    fixed_parameters = {
        'v_thresh': float('inf'),
        'cm': 1.0,
        'v_rest': 0.0
    }

    # pylint: disable=W0221
    def __init__(self, **params):
        """
        Initializes the neuron whose membrane potential is read out and
        normalized. The obligatory threshold voltage 'v_thresh' is set to
        infinity. The rising time constant is always smaller
        than the falling time constant. If tau_rise > tau_fall,
        "tau_rise" is interpreted as falling time constant and
        "tau_fall" as rising time constant.

        :param tau_rise: Rising time constant, default: 10.0 ms
        :param tau_fall: Falling time constant, default: 20.0 ms
        """
        super(PyNNPopulationRate, self).__init__(**params)

        self._cell = None
        self._weight = None
        self._rate = None

        self._create_device()
        self._calculate_weight()
        self._start_record_rate()

    @property
    def rate(self):
        """
        Returns the population firing rate
        """
        return self._rate

    def sim(self):  # pragma: no cover
        """
        Gets the simulator module to use
        """
        raise NotImplementedError("This method must be overridden in a derived class")

    def _update_parameters(self, params):
        super(PyNNPopulationRate, self)._update_parameters(params)
        self._parameters["tau_rise"], self._parameters["tau_fall"] = \
            sorted(self.get_parameters("tau_rise", "tau_fall").values())

    def _create_device(self):
        """
        Creates a LIF neuron with decaying-exponential post-synaptic currents
        and current-based synapses.
        """

        self._cell = self.sim().Population(1, self.sim().IF_curr_exp(
            **self.get_parameters(("tau_m", "tau_fall"),
                                  ("tau_syn_E", "tau_rise"),
                                  "v_thresh",
                                  "cm",
                                  "v_rest")))
        self.sim().initialize(self._cell, v=self._cell[0].v_rest)

    def _calculate_weight(self):
        """
        Calculates the weight of a neuron from the population to the device
        such that the area below the resulting PSP is 1. The exact shape of a
        PSP can be found e.g. in Bytschok, I., Diploma thesis.
        """
        tau_c = (1. / self._cell[0].tau_syn_E - 1. / self._cell[0].tau_m) ** -1
        t_end = -np.log(1e-10) * self._cell[0].tau_m
        x_new = np.arange(0., t_end, 0.1)
        y_new = tau_c / self._cell[0].cm * (np.exp(
                -x_new / self._cell[0].tau_m) - np.exp(
                -x_new / self._cell[0].tau_syn_E))
        self._weight = 1.0 / simps(y_new, dx=self.sim().get_time_step())

    def _start_record_rate(self):
        """
        Records the rate of a neuronal population
        """
        self._cell.record('v')

    # No connection parameters necessary for this device
    # pylint: disable=W0613
    def connect(self, neurons):
        """
        Connects the neurons specified by "neurons" to the
        device.

        :param neurons: must be a Population, PopulationView or
            Assembly object
        """

        connector = self.sim().AllToAllConnector()
        synapse_type = self.sim().StaticSynapse(
            weight=self._weight * 1000, delay=self.sim().get_time_step())

        return self.sim().Projection(presynaptic_population=neurons,
                                     postsynaptic_population=self._cell,
                                     connector=connector, receptor_type='excitatory',
                                     synapse_type=synapse_type)

    def _disconnect(self):
        """
        Disconnects the rate recorder by disabling voltage recording and setting
        rate to 0 since we cannot delete the neuron or synapses via PyNN.
        """
        if self._cell:
            self._cell.record(None)
            self._cell = None
            self._rate = 0

    # simulation time not necessary for this device
    # pylint: disable=unused-argument
    def refresh(self, time):
        """
        Refreshes the rate value

        :param time: The current simulation time
        """
        self._rate = self._cell.get_data('v', clear=True)[-1, -1]
