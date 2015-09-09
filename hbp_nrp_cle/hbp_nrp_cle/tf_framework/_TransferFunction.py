"""
Defines the base class for a transfer function
"""

import inspect
import textwrap
import logging
from . import config
from hbp_nrp_cle.common import SimulationFactoryCLEError


logger = logging.getLogger(__name__)

__author__ = 'GeorgHinkel'


class TransferFunction(object):
    """
    Represents the base class for a transfer function
    """

    def __init__(self):
        self._params = []
        self._func = None
        self.__source = None
        self.__elapsed_time = 0.0
        self.__updated_since_last_error = True
        self.__publish_error_callback = None

    @property
    def name(self):
        """
        Gets the name of the Transfer Function

        :return: The name of the Transfer Function as string
        """
        return self._func.__name__

    @property
    def params(self):
        """
        Gets the simulation adapters for this transfer function, either robot subscriber, publisher
        or neuronal simulator device adapters

        :return: A list of adapters
        """
        return self._params

    @property
    def elapsed_time(self):
        """
        Gets the elapsed time for this Transfer Function

        :return: The elapsed time for this TF in seconds
        """
        return self.__elapsed_time

    @elapsed_time.setter
    def elapsed_time(self, value):
        """
        Sets the elapsed time for this Transfer Function
        """
        self.__elapsed_time = value

    @property
    def updated(self):
        """
        Gets the update flag of the transfer function.

        :return: A boolean that tells if the source code was updated
                 but has its loading still pending, it is
                 True if the source code was updated but not loaded by an exec statement
                 False otherwise
        """

        return self.__updated_since_last_error

    @updated.setter
    def updated(self, status):
        """
        Sets the update flag of this transfer function.

        :param status: Boolean reflecting the current status of the transfer function
        """
        self.__updated_since_last_error = status

    @property
    def source(self):
        """
        Gets the source code of this transfer function.

        :return: A string containing the transfer function source code correctly indented.

        .. WARNING:: The source code is read from the generated file based on the template.
                     If someone patches the transfer function, the patched code will not be
                     returned (see python inspect module documentation).
        """

        if (self.__source is None):
            self.__source = "# Transfer function not loaded properly."
            if (self._func):
                try:
                    self.__source = inspect.getsource(self._func)
                except IOError as e:
                    error_msg = "The transfer function source code cannot be retrieved."
                    logger.error(error_msg)
                    logger.error(e)
                    self.__source = "# " + error_msg

        return textwrap.dedent(self.__source)

    @source.setter
    def source(self, source):
        """
        Sets the source code of this transfer function.

        :param source: String containing transfer function's source code
        """
        self.__source = source
        self.__updated_since_last_error = True

    def publish_error(self, tf_run_exception):
        """
        Publishes an error message on the error/transfer_function ROS Topic
        to inform the client.

        :param tf_run_exception: exception raised due to run time failure
        """
        error_publisher = config.active_node.publish_error_callback
        if (error_publisher and self.updated):  # avoid duplicate error messages
            self.updated = False
            logger.error(
              "Error while running transfer function " + self.name + ":\n"
              + str(tf_run_exception)
            )
            error_publisher(
                SimulationFactoryCLEError(
                    "Transfer Function",
                    "RunTime",
                     str(tf_run_exception),
                    self.name,
                )
            )
