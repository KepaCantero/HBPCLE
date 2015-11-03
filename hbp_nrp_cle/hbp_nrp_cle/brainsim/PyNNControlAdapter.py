'''
PyNNControlAdapter.py
moduleauthor: probst@fzi.de
'''

from .BrainInterface import IBrainControlAdapter
import pyNN.nest as sim
from . import BrainLoader
import logging
from os import path

logger = logging.getLogger(__name__)

__author__ = 'DimitriProbst'


class PyNNControlAdapter(IBrainControlAdapter):
    """
    Represents a controller object for the neuronal simulator
    """

    def __init__(self):
        """
        Initializes the PyNN control adapter
        """
        self.__is_initialized = False
        self.__is_alive = False
        self.__rank = None

    def load_brain(self, network_file, populations):
        """
        Loads the neuronal network contained in the given file

        :param network_file: The path to the neuronal network file
        :param populations: The populations to create
        """
        self.__is_alive = True
        extension = path.splitext(network_file)[1]
        if extension == ".py":
            self.__load_python_brain(network_file, populations)
        elif extension == ".h5":
            self.__load_h5_brain(network_file, populations)
        else:
            msg = "Neuronal network format {0} not supported".format(extension)
            raise Exception(msg)

    def __load_h5_brain(self, network_file, populations):
        """
        Loads the brain model in the given h5 file

        :param network_file: The path to the .5h file containing the network
        :param populations: A named list of populations to create
        """
        if not self.__is_initialized:
            self.initialize()
        BrainLoader.load_h5_network(network_file, populations)

    def __load_python_brain(self, network_file, populations):
        """
        Loads the brain model specified in the given Python script

        :param network_file: The Python file containing the network
        :param populations: A named list of populations to create
        """
        if not self.__is_initialized:
            self.initialize()
        BrainLoader.load_py_network(network_file, populations)

    def initialize(self, **params):
        """
        Initializes the neuronal simulator

        :param timestep: The timestep used for the neuronal simulation
        :param min_delay: The minimum delay
        :param max_delay: The maximum delay
        :param threads: The amount of threads that should be used to run the simulation
        :param rng_seeds: The rng seeds for the simulation
        :return: True if the simulator is initialized, otherwise False
        """
        if not self.__is_initialized:
            timestep = params.get('timestep', 0.1)
            min_delay = params.get('min_delay', 0.1)
            max_delay = params.get('max_delay', 20.0)
            threads = params.get('threads', 1)
            rng_seeds = params.get('rng_seeds', [1234])
            self.__rank = sim.setup(timestep=timestep, min_delay=min_delay,
                                    max_delay=max_delay, threads=threads,
                                    rng_seeds=rng_seeds)
            self.__is_initialized = True
            logger.info("neuronal simulator initialized")
        else:
            logger.warn("trying to initialize an already initialized controller")
        return self.__is_initialized

    def is_alive(self):  # -> bool:
        """
        Gets a status whether the neuronal simulator is still alive

        :return: True if the simulator is alive, otherwise False
        """
        return self.__is_alive

    def run_step(self, dt):  # -> None:
        """
        Runs the neuronal simulator for the given amount of simulated time

        :param dt: the simulated time in milliseconds
        """
        sim.run(dt)

    def shutdown(self):  # -> None:
        """
        Shuts down the neuronal simulator
        """
        self.__is_alive = False
        sim.end()
        logger.info("neuronal simulator ended")

    def reset(self):  # -> None:
        """
        Resets the neuronal simulator
        """
        logger.info("neuronal simulator reset")
