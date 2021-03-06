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
from hbp_nrp_cle.brainsim.pynn_nest.devices.__PyNNNestACSource import PyNNNestACSource
from hbp_nrp_cle.brainsim.pynn_nest.devices.__PyNNNestDCSource \
    import PyNNNestDCSource, IntegratedNestDCCurrentGenerator

import unittest
from mock import patch, Mock

__author__ = 'Georg Hinkel'


@patch("hbp_nrp_cle.brainsim.pynn_nest.devices.__NestDeviceGroup.nest")
class TestNestDeviceGroup(unittest.TestCase):

    def __create_mock_with_id(self, i):
        m = Mock()
        m._device = [i]
        m.all_cells = [i]
        return m

    @patch("hbp_nrp_cle.brainsim.pynn_nest.devices.__PyNNNestACSource.PyNNNestACSource.sim")
    def setUp(self, mocked_sim):
        self.neurons = [self.__create_mock_with_id(i) for i in range(0, 5)]
        mocked_sim().ACSource.side_effect = self.neurons
        self.device = PyNNNestACSource.create_new_device_group(self.neurons, {})
        self.device.connect(self.neurons)
        self.device_ids = self.device._device_ids

        self.assertEqual(len(self.neurons), len(self.device_ids))
        for i in range(0, 5):
            self.assertEqual(i, self.device_ids[i])

    def test_device_group_get_one_nest_get_status(self, mocked_nest):
        mocked_nest.GetStatus.return_value = 42
        frequency = self.device.frequency
        mocked_nest.GetStatus.assert_called_once_with(self.device_ids, "frequency")
        self.assertEqual(42, frequency)

    def test_device_group_get_transform_one_nest_get_status(self, mocked_nest):
        mocked_nest.GetStatus.return_value = [42000, 0, 8000, 15000]
        amplitude = self.device.amplitude
        mocked_nest.GetStatus.assert_called_once_with(self.device_ids, "amplitude")
        self.assertItemsEqual([42.0, 0.0, 8.0, 15.0], amplitude)

    def test_device_group_single_set_one_nest_set_status(self, mocked_nest):
        val = 42
        self.device.frequency = val
        self.assertEqual(1, mocked_nest.SetStatus.call_count)
        call_args = mocked_nest.SetStatus.call_args[0]
        self.assertEqual(self.device_ids, call_args[0])
        self.assertDictEqual({"frequency": 42}, call_args[1])

    def test_device_group_single_set_transform_one_nest_set_status(self, mocked_nest):
        val = 42
        self.device.amplitude = val
        self.assertEqual(1, mocked_nest.SetStatus.call_count)
        call_args = mocked_nest.SetStatus.call_args[0]
        self.assertEqual(self.device_ids, call_args[0])
        self.assertDictEqual({"amplitude": 42000.0}, call_args[1])

    def test_device_group_multiple_set_one_nest_set_status(self, mocked_nest):
        val = [42, 0, 8, 15, 0]
        self.device.frequency = val
        self.assertEqual(1, mocked_nest.SetStatus.call_count)
        call_args = mocked_nest.SetStatus.call_args[0]
        self.assertEqual(self.device_ids, call_args[0])
        self.assertEqual(5, len(call_args[1]))
        for i in range(0, 5):
            self.assertDictEqual({"frequency": val[i]}, call_args[1][i])

    def test_device_group_multiple_set_transform_one_nest_set_status(self, mocked_nest):
        val = [42, 0, 8, 15, 0]
        self.device.amplitude = val
        self.assertEqual(1, mocked_nest.SetStatus.call_count)
        call_args = mocked_nest.SetStatus.call_args[0]
        self.assertEqual(self.device_ids, call_args[0])
        self.assertEqual(5, len(call_args[1]))
        for i in range(0, 5):
            self.assertDictEqual({"amplitude": val[i] * 1000.0}, call_args[1][i])

    def test_active_set(self, _):

        self.device.active = False
        self.assertFalse(self.device.active)

        self.device.active = True
        self.assertTrue(self.device.active)

    @patch("hbp_nrp_cle.brainsim.pynn_nest.devices.__PyNNNestDCSource.nest")
    def test_integrated_generator_device_group(self, mock_nest_dc_source, mock_nest_device_group):
        device_property = "I_e"  # amplitude device property for IntegratedNestDCCurrentGenerator

        # set up
        mock_nest_dc_source.GetStatus.return_value = ({device_property: 1.0},)

        neurons = [self.__create_mock_with_id(i) for i in range(0, 5)]

        device_group = PyNNNestDCSource.create_new_device_group(neurons, {})
        device_group.connect(neurons)

        device_ids = device_group._device_ids
        self.assertEqual(len(neurons), len(device_ids))
        for i in range(0, 5):
            self.assertEqual(i, device_ids[i])

        # the device_type should be IntegratedNestDCCurrentGenerator
        self.assertEqual(device_group.device_type, IntegratedNestDCCurrentGenerator)

        vals = [42, 0, 8, 15, 0]

        # Set the amplitude of the generators
        # which in the case of IntegratedNestDCCurrentGenerator
        # corresponds to setting the generator's I_e property
        device_group.set("amplitude", vals)

        device_ids_, vals_ = mock_nest_device_group.SetStatus.call_args[0]

        # check that the correct device property has been used while setting
        self.assertTrue(all(map(lambda dict_: dict_.keys()[0] == device_property, vals_)))

