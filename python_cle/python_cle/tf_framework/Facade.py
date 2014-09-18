from . import config

from python_cle.brainsim.BrainInterface import IFixedFrequencySpikeGenerator, \
    INeuronVoltmeter, IPoissonSpikeGenerator, IPatternSpikeGenerator, ISpikeRecorder

from .Neuron2Robot import Neuron2Robot, MapNeuronParameter
from .Robot2Neuron import Robot2Neuron, MapRobotParameter
from . import TransferFunctionManager

__author__ = 'GeorgHinkel'

voltmeter = INeuronVoltmeter
fixed_frequency = IFixedFrequencySpikeGenerator
poisson = IPoissonSpikeGenerator
pattern = IPatternSpikeGenerator
recorder = ISpikeRecorder


def initialize(name):  # -> None:
    """
    Initializes and starts the TF node
    :param name: The name of the TF node
    """
    config.active_node.initialize(name)


def send_robot(topic, value):  # -> None:
    """
    Send data to the given robot topic
    :param topic: The robot topic
    :param value: The values sent to the robot
    """
    print("Sending ", value, " to robot ", topic)


def set_nest_adapter(nest_adapter):  # -> None:
    """
    Sets the brainsim adapter. Must be executed before tf node initialization
    :param nest_adapter: The brainsim adapter
    """
    config.active_node.nest_adapter = nest_adapter


def set_robot_adapter(robot_adapter):  # -> None:
    """
    Sets the robot adapter. Must be run before tf node initialization
    :param robot_adapter: The robot adapter
    """
    config.active_node.robot_adapter = robot_adapter

def start_new_tf_manager():
    config.active_node = TransferFunctionManager.TransferFunctionManager()