'''
PyNNCommunicationAdapter.py
moduleauthor: probst@fzi.de
'''

from .BrainInterface import IBrainCommunicationAdapter, \
    ILeakyIntegratorAlpha, ISpikeDetector, IPoissonSpikeGenerator, \
    IDCSource, IACSource, INCSource, \
    ILeakyIntegratorExp, IPopulationRate, IFixedSpikeGenerator
from .__devices.PyNNPoissonSpikeGenerator import PyNNPoissonSpikeGenerator
from .__devices.PyNNFixedSpikeGenerator import PyNNFixedSpikeGenerator
from .__devices.PyNNDCSource import PyNNDCSource
from .__devices.PyNNACSource import PyNNACSource
from .__devices.PyNNNCSource import PyNNNCSource
from .__devices.PyNNLeakyIntegratorAlpha import PyNNLeakyIntegratorAlpha
from .__devices.PyNNLeakyIntegratorExp import PyNNLeakyIntegratorExp
from .__devices.PyNNPopulationRate import PyNNPopulationRate
from .__devices.PyNNSpikeRecorder import PyNNSpikeRecorder
from .__devices.PyNNDeviceGroup import PyNNDeviceGroup

__author__ = 'DimitriProbst'


class PyNNCommunicationAdapter(IBrainCommunicationAdapter):
    """
    Represents the communication adapter to the neuronal simulator
    """
    # In this dictionary, the association of spike generator types to classes
    # implementing their functionality is established
    __device_dict = {IFixedSpikeGenerator: PyNNFixedSpikeGenerator,
                     IPoissonSpikeGenerator: PyNNPoissonSpikeGenerator,
                     IDCSource: PyNNDCSource,
                     IACSource: PyNNACSource,
                     INCSource: PyNNNCSource,
                     ILeakyIntegratorAlpha: PyNNLeakyIntegratorAlpha,
                     ILeakyIntegratorExp: PyNNLeakyIntegratorExp,
                     IPopulationRate: PyNNPopulationRate,
                     ISpikeDetector: PyNNSpikeRecorder}

    def __init__(self):
        """
        Initializes the communication adapter
        """
        self.__generator_devices = []
        self.__detector_devices = []
        self.__is_initialized = False

    def initialize(self):
        """
        Marks the PyNN adapter as initialized
        """
        self.__is_initialized = True

    def register_spike_source(self, populations, spike_generator_type, **params):
        """
        Requests a communication object with the given spike generator type
        for the given set of neurons
        :param populations: A reference to the populations to which the spike generator
        should be connected
        :param spike_generator_type: A spike generator type (see documentation
        or a list of allowed values)
        :param params: A dictionary of configuration parameters
        :return: A communication object or a group of objects
        """
        if not isinstance(populations, list):
            device = PyNNCommunicationAdapter.__device_dict[
                spike_generator_type](**params)
            device.connect(populations, **params)
            self.__generator_devices.append(device)
            return device
        else:
            device_list = []
            for pop in populations:
                device = PyNNCommunicationAdapter.__device_dict[
                    spike_generator_type](**params)
                device.connect(pop, **params)
                device_list.append(device)
            self.__generator_devices += device_list
            device_group = PyNNDeviceGroup(device_list)
            return device_group

    def register_spike_sink(self, populations, spike_detector_type, **params):
        '''
        Requests a communication object with the given spike detector type
        for the given set of neurons
        :param populations: A reference to the populations which should be connected
        to the spike detector
        :param spike_detector_type: A spike detector type (see documentation
        for a list of allowed values)
        :param params: A dictionary of configuration parameters
        :return: A Communication object or a group of objects
        '''
        if not isinstance(populations, list):
            device = PyNNCommunicationAdapter.__device_dict[
                spike_detector_type](**params)
            device.connect(populations, **params)
            self.__detector_devices.append(device)
            return device
        else:
            device_list = []
            for pop in populations:
                device = PyNNCommunicationAdapter.__device_dict[
                    spike_detector_type](**params)
                device.connect(pop, **params)
                device_list.append(device)
            self.__detector_devices += device_list
            device_group = PyNNDeviceGroup(device_list)
            return device_group

    def refresh_buffers(self, t):
        """
        Refreshes all detector buffers
        """
        for detector in self.__detector_devices:
            if hasattr(detector, "refresh"):
                detector.refresh(t)

    @property
    def detector_devices(self):
        """
        Gets the created detector __devices
        """
        return self.__detector_devices

    @property
    def generator_devices(self):
        """
        Gets the created spike detector __devices
        """
        return self.__generator_devices

    @property
    def is_initialized(self):
        """
        Gets a value indicating whether initialize has been called
        """
        return self.__is_initialized