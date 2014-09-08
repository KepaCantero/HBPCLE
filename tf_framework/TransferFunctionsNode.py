__author__ = 'GeorgHinkel'

from robotsim.RobotInterface import Topic, IRobotCommunicationAdapter
from brainsim.BrainInterface import IBrainCommunicationAdapter
from .Neuron2Robot import Neuron2Robot
from .Robot2Neuron import Robot2Neuron
from .TransferFunctionsInterface import ITransferFunctionsNode


class TransferFunctionNode(ITransferFunctionsNode):
    """
    Represents a transfer functions node
    """

    def __init__(self):
        self.__n2r = []
        self.__r2n = []
        self.__robotAdapter = None
        self.__nestAdapter = None
        self.__initialized = False

    def __get_n2r(self):
        return self.__n2r

    def __get_r2n(self):
        return self.__r2n

    def run_neuron_to_robot(self, t):
        """
        Runs the transfer functions from the neuronal simulator towards the robot
        :param t: The simulation time
        """
        for _n2r in self.__n2r:
            assert isinstance(_n2r, Neuron2Robot)
            _n2r.run(t)

    def run_robot_to_neuron(self, t):
        """
        Runs the transfer functions from the world simulation towards the neuronal simulation
        :param t:  The simulation time
        """
        for _r2n in self.__r2n:
            assert isinstance(_r2n, Robot2Neuron)
            _r2n.run(t)

    def initialize(self, name):
        """
        Initializes the transfer Function node with the given name
        :param name: The name for this transfer function node
        """
        if self.__nestAdapter is None:
            raise Exception("No brain simulation adapter has been specified")

        if self.__robotAdapter is None:
            raise Exception("No robot simulation adapter has been specified")

        assert isinstance(self.__nestAdapter, IBrainCommunicationAdapter)
        assert isinstance(self.__robotAdapter, IRobotCommunicationAdapter)

        self.__nestAdapter.initialize()
        self.__robotAdapter.initialize(name)

        for _n2r in self.__n2r:
            assert isinstance(_n2r, Neuron2Robot)
            _n2r.replace_params()

            _n2r.main_robot_topic = self.__robotAdapter.register_publish_topic(_n2r.main_robot_topic)
            for i in range(0, len(_n2r.robot_topics)):
                _n2r.robot_topics[i] = self.__robotAdapter.register_publish_topic(_n2r.robot_topics[i])

            for i in range(0, len(_n2r.neuron_params)):
                item = _n2r.neuron_params[i]
                _n2r.neuron_params[i] = self.__nestAdapter.register_consume_spikes(item[0], item[1])

        for _r2n in self.__r2n:
            assert isinstance(_r2n, Robot2Neuron)
            _r2n.check_params()

            for i in range(0, len(_r2n.params)):
                item = _r2n.params[i]
                if isinstance(item, Topic):
                    _r2n.params[i] = self.__robotAdapter.register_subscribe_topic(item)
                else:
                    _r2n.params[i] = self.__nestAdapter.register_generate_spikes(item[0], item[1])

    def __get_robot_adapter(self):
        return self.__robotAdapter

    def __set_robot_adapter(self, robot_adapter):
        if self.__initialized:
            raise Exception("Cannot exchange robot adapter after node has been initialized!")
        else:
            assert isinstance(robot_adapter, IRobotCommunicationAdapter)
            self.__robotAdapter = robot_adapter

    def __get_nest_adapter(self):
        return self.__nestAdapter

    def __set_nest_adapter(self, nest_adapter):
        if self.__initialized:
            raise Exception("Cannot exchange brainsim adapter after node has been initialized!")
        else:
            assert isinstance(nest_adapter, IBrainCommunicationAdapter)
            self.__nestAdapter = nest_adapter

    n2r = property(__get_n2r)

    r2n = property(__get_r2n)

    robot_adapter = property(__get_robot_adapter, __set_robot_adapter)

    nest_adapter = property(__get_nest_adapter, __set_nest_adapter)