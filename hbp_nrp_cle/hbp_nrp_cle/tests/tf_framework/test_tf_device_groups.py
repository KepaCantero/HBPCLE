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
import hbp_nrp_cle.tf_framework as nrp
from hbp_nrp_cle.tf_framework import config
from hbp_nrp_cle.tests.tf_framework.TestDevice import TestDevice
from hbp_nrp_cle.tests.tf_framework.husky import Husky

from hbp_nrp_cle.mocks.robotsim._MockRobotCommunicationAdapter import MockRobotCommunicationAdapter, \
    MockPublishedTopic
from hbp_nrp_cle.mocks.brainsim._MockBrainCommunicationAdapter import MockBrainCommunicationAdapter
from hbp_nrp_cle.tests.tf_framework.MockBrain import MockPopulation
from mock import patch, Mock

import unittest
import numpy as np

__author__ = 'GeorgHinkel'

MockOs = Mock()
MockOs.environ = {'NRP_SIMULATION_DIR': '/somewhere/near/the/rainbow'}
@patch("hbp_nrp_cle.common.os", new=MockOs)
class Test2(unittest.TestCase):
    def test_all_right(self):

        nrp.start_new_tf_manager()

        brain = MockBrainCommunicationAdapter()
        robot = MockRobotCommunicationAdapter()

        @nrp.MapSpikeSink("neuron0", nrp.map_neurons(range(0, 2), lambda i: nrp.brain.actors[i]),
                          nrp.leaky_integrator_alpha,
                          v_rest=1.0, updates=[(1.0, [0.3, 0.0])])
        @nrp.Neuron2Robot(Husky.RightArm.pose)
        def right_arm(t, neuron0):
            return np.sum(neuron0.voltage) * 1.345

        # Here is a another transfer function from neurons to robot messages
        # This time, the neuron parameter is explicitly mapped to an array of neurons
        # More precisely, the parameter is mapped to a group of __devices that are each connected to a single neuron
        # The neuron2 parameter will thus be a list of recorders
        @nrp.MapSpikeSink("neurons", nrp.chain_neurons(nrp.brain.actors[slice(2, 4, 1)],
                                                       nrp.brain.actors[slice(4, 6, 1)]),
                          nrp.leaky_integrator_alpha,
                          updates=[(1.0, [0.4, 0.4])], v_rest=1.0)
        @nrp.Neuron2Robot(Husky.LeftArm.twist)
        def left_arm_tw(t, neurons):
            if neurons[0].voltage < 0.678:
                if neurons[1].voltage > 0.345:
                    return 0.756
                else:
                    return 1.123
            else:
                if neurons[1].voltage < 0.789:
                    return 0.632
                else:
                    return 0.256

        nrp.set_nest_adapter(brain)
        nrp.set_robot_adapter(robot)

        brain.__dict__["actors"] = MockPopulation(range(0, 60))
        brain.__dict__["sensors"] = MockPopulation(range(45, 645))
        config.brain_root = brain

        nrp.initialize("MyTransferFunctions")

        husky_right_arm = right_arm.topic
        husky_left_arm = left_arm_tw.topic

        brain.refresh_buffers(0.5)
        robot.refresh_buffers(0.5)
        config.active_node.run_neuron_to_robot(0.5)
        config.active_node.run_robot_to_neuron(0.5)

        brain.refresh_buffers(1.5)
        robot.refresh_buffers(1.5)
        config.active_node.run_neuron_to_robot(1.5)
        config.active_node.run_robot_to_neuron(1.5)

        self.assertIsInstance(husky_right_arm, MockPublishedTopic)
        self.assertIsInstance(husky_left_arm, MockPublishedTopic)

        self.assertEqual(len(husky_right_arm.sent), 2)
        self.assertEqual(len(husky_left_arm.sent), 2)

        self.assertEqual(husky_right_arm.sent[0], 1.345 * 2.0)
        self.assertEqual(husky_right_arm.sent[1], 1.345 * 0.3)

        self.assertEqual(husky_left_arm.sent[0], 0.256)
        self.assertEqual(husky_left_arm.sent[1], 0.756)

        config.active_node.reset()


if __name__ == "__main__":
    unittest.main()
