'''
Implementation of PyNNFixedSpikeGenerator
moduleauthor: probst@fzi.de
'''

from hbp_nrp_cle.brainsim.common.devices import AbstractBrainDevice
from hbp_nrp_cle.brainsim.BrainInterface import IFixedSpikeGenerator
from hbp_nrp_cle.brainsim.pynn import simulator as sim
import numpy as np

__author__ = 'Dimitri Probst, Sebastian Krach, Georg Hinkel'


class PyNNFixedSpikeGenerator(AbstractBrainDevice, IFixedSpikeGenerator):
    """
    Represents a spike generator which generated equidistant
    spike times at a given frequency
    """

    default_parameters = {
        'initial_rate': 0.0,
        'cm': 1.0,
        'tau_m': 1000.0,
        'tau_refrac': sim.state.dt,
        'v_thresh': -50.0,
        'v_reset': -100.0,
        'v_rest': -100.0,
        'connector': None,
        'weights': None,
        'delays': None,
        'source': None,
        'target': 'excitatory',
        'synapse_dynamics': None,
        'label': None,
        'rng': None
    }

    # pylint: disable=W0221
    def __init__(self, **params):
        """
        Initializes a Fixed spike generator.

        :param rate: Rate/frequency of spike train, default: 0.0 Hz
        :param connector: a PyNN Connector object, or, if neurons is
            a list of two populations, a list of two Connector objects
        :param source: string specifying which attribute of the presynaptic
            cell signals action potentials
        :param target: string specifying which synapse on the postsynaptic cell
            to connect to: excitatory or inhibitory. If neurons is a list of
            two populations, target is ['excitatory', 'inhibitory'], dafault is
            excitatory
        :param synapse_dynamics: a PyNN SynapseDy
        :param label: label of the Projection object
        :param rng: RNG object to be used by the Connector
            synaptic plasticity mechanisms to use
        """
        super(PyNNFixedSpikeGenerator, self).__init__(**params)

        self._generator = None
        self._currentsource = None
        self._calculate_rate_and_current = self._setup_rate_and_current_calculation()

        (self._rate,
         self._current) = self._calculate_rate_and_current(self._parameters["initial_rate"])

        self.create_device()

    @property
    def rate(self):
        """
        Returns the frequency of the Fixed spike generator
        """
        return self._rate

    # pylint: disable=unused-argument
    @rate.setter
    def rate(self, value):  # pragma: no cover
        """
        Sets the frequency of the Fixed spike generator

        :param value: float
        """
        raise RuntimeError("Resetting this property is currently not supported by PyNN")

    def create_device(self):
        """
        Create a fixed spike-distance device
        """

        self._generator = sim.Population(1, sim.IF_curr_exp, self.get_parameters("cm",
                                                                                 "tau_m",
                                                                                 "v_thresh",
                                                                                 "v_reset",
                                                                                 "v_rest"))
        sim.initialize(self._generator, 'v', self._generator[0].v_rest)

        self._currentsource = sim.DCSource(amplitude=self._current)
        self._currentsource.inject_into(self._generator)

    def _setup_rate_and_current_calculation(self):
        """
        This method sets up the calculation of the suitable current based on specified spiking
        rate values. As this calculation is dependent on neuron parameters which are only set
        once, this method returns a callable which expects the desired spiking rate and returns a
        tuple of closest achievable rate and the appropriate current in nA.

        :return: a callable function: float --> (float, float)
        """
        tau_m, tau_refrac, cm, v_thresh, v_rest = \
            self.get_parameters("tau_m", "tau_refrac", "cm", "v_thresh", "v_rest").values()

        def calculate_rate_and_current(rate):
            """
            Returns current in nA corresponding to frequency "rate". If the specified spiking rate
            is not achievable due to the neuron configuration the current is determined for the
            possible maximum.

            :param rate: Frequency in Hz
            :return: The frequency which results from injecting the configured neuron with the
                    resulting current in Hz.
            :return: The resulting dc current
            """
            nom = (cm / tau_m) * (v_thresh - v_rest)
            denom = 1.0
            if rate != 0.0:
                inter_time = 1000.0 / rate
                if inter_time < 10 * tau_refrac:
                    rate = 100.0 / tau_refrac
                    inter_time = 10 * tau_refrac
                denom = 1.0 - np.exp((tau_refrac - inter_time) / tau_m)
            return rate, nom / denom

        return calculate_rate_and_current

    def connect(self, neurons):
        """
        Connects the neurons specified by "neurons" to the
        device. The connection structure is specified via the
        PyNN connection object "connector". If "connector" is None,
        the weights and delays between the neurons and the device
        are sampled from a uniform distribution.

        :param neurons: must be a Population, PopulationView or
            Assembly object
        """
        # As connection parameters depend on the passed neuron structure the parameters are
        # evaluated in the connect method.
        if not "connector" in self._parameters or not self._parameters["connector"]:
            weights = self._parameters["weights"]
            if not weights:
                weights = self._get_default_weights(neurons.conductance_based)
                self._parameters["weights"] = weights
            delays = self._parameters["delays"]
            self._parameters["connector"] = sim.AllToAllConnector(weights=weights, delays=delays)
        else:
            conn = self._parameters["connector"]
            if isinstance(conn, dict):
                weights = self._parameters["weights"]
                if not weights:
                    weights = conn.get("weights")
                if not weights:
                    weights = self._get_default_weights(neurons.conductance_based)
                delays = conn.get("delays")
                if not delays:
                    delays = self._parameters["delays"]
                self._parameters["delays"] = delays
                self._parameters["weights"] = weights
                if conn.get("mode") == "OneToOne":
                    self._parameters["connector"] = \
                        sim.OneToOneConnector(weights=weights, delays=delays)
                elif conn.get("mode") == "AllToAll":
                    self._parameters["connector"] = \
                        sim.AllToAllConnector(weights=weights, delays=delays)
                elif conn.get("mode") == "Fixed":
                    self._parameters["connector"] = \
                        sim.FixedNumberPreConnector(conn.get("n", 1), weights, delays)
                else:
                    raise Exception("Invalid connector mode")

        return sim.Projection(presynaptic_population=self._generator,
                              postsynaptic_population=neurons,
                              **self.get_parameters(("method", "connector"),
                                                     "source",
                                                     "target",
                                                     "synapse_dynamics",
                                                     "label",
                                                     "rng"))

    def _update_parameters(self, params):
        """
        This method updates the device parameter dictionary with the provided parameter
        dictionary. The dictionary has to be validated before as this method assumes it to be
        correct.

        Overriding subclasses can provide additional configuration parameter adaption as this
        method is called before the brain simulator devices are constructed.

        :param params: The validated parameter dictionary
        """
        super(PyNNFixedSpikeGenerator, self)._update_parameters(params)

        if isinstance(self._parameters["synapse_dynamics"], dict):
            dyn = self._parameters["synapse_dynamics"]
            if dyn["type"] == "TsodyksMarkram":
                self._parameters["synapse_dynamics"] = \
                    sim.SynapseDynamics(sim.TsodyksMarkramMechanism(
                        U=dyn["U"], tau_rec=dyn["tau_rec"], tau_facil=dyn["tau_facil"]))
        if not self._parameters["delays"]:
            self._parameters["delays"] = sim.RandomDistribution('uniform', [0.1, 2.0])

    def _get_default_weights(self, conductance_based):
        """
        Gets the default weights distribution

        :param conductance_based: Indicates whether the connected neurons
        are conductance based
        """
        if self._parameters["target"] == 'excitatory':
            weights = sim.RandomDistribution('uniform', [0.0, 0.01])
        else:
            if conductance_based:
                weights = sim.RandomDistribution('uniform', [0.0, 0.01])
            else:
                weights = sim.RandomDistribution('uniform', [-0.01, -0.0])
        return weights
