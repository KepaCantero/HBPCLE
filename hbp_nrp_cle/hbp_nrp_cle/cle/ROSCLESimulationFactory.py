"""
Advertise a ROS service to start new simulations.
"""

import logging
import rospy
import imp
import threading
import os
# This package comes from the catkin package ROSCLEServicesDefinitions
# in the GazeboRosPackage folder at the root of the CLE (this) repository.
from ROSCLEServicesDefinitions import srv

__author__ = "Lorenzo Vannucci, Stefan Deser, Daniel Peppicelli"
logger = logging.getLogger(__name__)


class ROSCLESimulationFactory(object):
    """
    The purpose of this class is to start simulation thread and to
    provide a ROS service for that. Only one simulation can run at a time.
    """

    ROS_CLE_NODE_NAME = "ros_cle_simulation"
    ROS_CLE_URI_PREFIX = "/" + ROS_CLE_NODE_NAME

    def __init__(self):
        """
        Create a CLE simulation factory.
        """
        logger.debug("Creating new CLE server.")
        self.running_simulation_thread = None

    def run(self):
        """
        Start the factory and wait indefinitely. (see rospy.spin documentation)
        """
        rospy.init_node(self.ROS_CLE_NODE_NAME)
        rospy.Service(
            self.ROS_CLE_URI_PREFIX + "/start_new_simulation",
            srv.start_new_simulation,
            self.start_new_simulation)
        rospy.spin()

    def start_new_simulation(self, service_request):
        """
        Handler for the ROS service. Spawn a new simulation.
        Warning: Multiprocesses can not be used: https://code.ros.org/trac/ros/ticket/972
        :param: service_request: ROS service message (defined in hbp ROS packages)
        """
        logger.info("Start new simulation request")
        result = False
        error_message = ""
        if ((self.running_simulation_thread is None) or
                (not self.running_simulation_thread.is_alive())):
            logger.info("No simulation running, starting a new simulation.")
            # Avoid zombie threads
            if (self.running_simulation_thread is not None):
                # The join should always work since we checked previously that
                # the thread is not running (with the is_alive() call).
                self.running_simulation_thread.join(timeout=1)

            # Currently, gazebo enters an infinite loop when restarting. This call
            # should be cleaned when the bug will be fixed.
            os.system("/etc/init.d/gzserver restart")
            os.system("/etc/init.d/gzbridge restart")

            # In the future, it would be great to move the CLE script generation logic here.
            # For the time beeing, we rely on the calling process to send us this thing.
            self.running_simulation_thread = threading.Thread(
                target=self.simulation,
                args=(service_request.environment_file,
                      service_request.generated_cle_script_file))
            self.running_simulation_thread.daemon = True
            logger.info("Spawning new thread that will manage the experiment execution.")
            self.running_simulation_thread.start()
            result = True
        else:
            error_message = """Trying to initialize a new simulation even though the
                previous one has not been terminated."""
            logger.error(error_message)
            result = False
        return [result, error_message]

    # pylint: disable=R0201
    def simulation(self, environment_file, generated_cle_script_file):
        """
        Main simulation method. Start the simulation from the given script file.
        :param: environment_file: Gazebo world file containing
                                  the environment (without the robot)
        :param: generated_cle_script_file: Generated CLE python script (main loop)
        """
        logger.info("Preparting new simulation with environment file: " +
                    environment_file +
                    " and generated script file " +
                    generated_cle_script_file +
                    ".")
        logger.info("Starting the experiment closed loop engine.")
        experiment_generated_script = imp.load_source(
            'experiment_generated_script', generated_cle_script_file)
        experiment_generated_script.cle_function(environment_file)


if __name__ == '__main__':
    server = ROSCLESimulationFactory()
    server.run()
    logger.info("CLE Server exiting.")