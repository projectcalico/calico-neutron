# Copyright (c) 2014 OpenStack Foundation, all rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from neutron import context
from neutron.db import models_v2
from neutron.extensions import portbindings
from neutron.openstack.common import uuidutils
from neutron.plugins.ml2 import db as ml2_db
from neutron.plugins.ml2 import driver_api as api
from neutron.plugins.ml2 import models
from neutron.tests.unit import testlib_api


class Ml2DBTestCase(testlib_api.SqlTestCase):

    def setUp(self):
        super(Ml2DBTestCase, self).setUp()
        self.ctx = context.get_admin_context()

    def _setup_neutron_network(self, network_id):
        with self.ctx.session.begin(subtransactions=True):
            self.ctx.session.add(models_v2.Network(id=network_id))

    def _setup_neutron_port(self, network_id, port_id):
        with self.ctx.session.begin(subtransactions=True):
            port = models_v2.Port(id=port_id,
                                  network_id=network_id,
                                  mac_address='foo_mac_address',
                                  admin_state_up=True,
                                  status='DOWN',
                                  device_id='',
                                  device_owner='')
            self.ctx.session.add(port)

    def _setup_neutron_portbinding(self, port_id, vif_type, host):
        with self.ctx.session.begin(subtransactions=True):
            self.ctx.session.add(models.PortBinding(port_id=port_id,
                                                    vif_type=vif_type,
                                                    host=host))

    def _create_segments(self, segments, is_seg_dynamic=False):
        network_id = 'foo-network-id'
        self._setup_neutron_network(network_id)
        for segment in segments:
            ml2_db.add_network_segment(
                self.ctx.session, network_id, segment,
                is_dynamic=is_seg_dynamic)

        net_segments = ml2_db.get_network_segments(
                           self.ctx.session, network_id,
                           filter_dynamic=is_seg_dynamic)

        for segment_index, segment in enumerate(segments):
            self.assertEqual(segment, net_segments[segment_index])

        return net_segments

    def test_network_segments_for_provider_network(self):
        segment = {api.NETWORK_TYPE: 'vlan',
                   api.PHYSICAL_NETWORK: 'physnet1',
                   api.SEGMENTATION_ID: 1}
        self._create_segments([segment])

    def test_network_segments_is_dynamic_true(self):
        segment = {api.NETWORK_TYPE: 'vlan',
                   api.PHYSICAL_NETWORK: 'physnet1',
                   api.SEGMENTATION_ID: 1}
        self._create_segments([segment], is_seg_dynamic=True)

    def test_network_segments_for_multiprovider_network(self):
        segments = [{api.NETWORK_TYPE: 'vlan',
                    api.PHYSICAL_NETWORK: 'physnet1',
                    api.SEGMENTATION_ID: 1},
                    {api.NETWORK_TYPE: 'vlan',
                     api.PHYSICAL_NETWORK: 'physnet1',
                     api.SEGMENTATION_ID: 2}]
        self._create_segments(segments)

    def test_get_segment_by_id(self):
        segment = {api.NETWORK_TYPE: 'vlan',
                   api.PHYSICAL_NETWORK: 'physnet1',
                   api.SEGMENTATION_ID: 1}

        net_segment = self._create_segments([segment])[0]
        segment_uuid = net_segment[api.ID]

        net_segment = ml2_db.get_segment_by_id(self.ctx.session, segment_uuid)
        self.assertEqual(segment, net_segment)

    def test_get_segment_by_id_result_not_found(self):
        segment_uuid = uuidutils.generate_uuid()
        net_segment = ml2_db.get_segment_by_id(self.ctx.session, segment_uuid)
        self.assertIsNone(net_segment)

    def test_delete_network_segment(self):
        segment = {api.NETWORK_TYPE: 'vlan',
                   api.PHYSICAL_NETWORK: 'physnet1',
                   api.SEGMENTATION_ID: 1}

        net_segment = self._create_segments([segment])[0]
        segment_uuid = net_segment[api.ID]

        ml2_db.delete_network_segment(self.ctx.session, segment_uuid)
        # Get segment and verify its empty
        net_segment = ml2_db.get_segment_by_id(self.ctx.session, segment_uuid)
        self.assertIsNone(net_segment)

    def test_add_port_binding(self):
        network_id = 'foo-network-id'
        port_id = 'foo-port-id'
        self._setup_neutron_network(network_id)
        self._setup_neutron_port(network_id, port_id)

        port = ml2_db.add_port_binding(self.ctx.session, port_id)
        self.assertEqual(port_id, port.port_id)
        self.assertEqual(portbindings.VIF_TYPE_UNBOUND, port.vif_type)

    def test_get_port_binding_host(self):
        network_id = 'foo-network-id'
        port_id = 'foo-port-id'
        host = 'fake_host'
        vif_type = portbindings.VIF_TYPE_UNBOUND
        self._setup_neutron_network(network_id)
        self._setup_neutron_port(network_id, port_id)
        self._setup_neutron_portbinding(port_id, vif_type, host)

        port_host = ml2_db.get_port_binding_host(port_id)
        self.assertEqual(host, port_host)

    def test_get_port_binding_host_multiple_results_found(self):
        network_id = 'foo-network-id'
        port_id = 'foo-port-id'
        port_id_one = 'foo-port-id-one'
        port_id_two = 'foo-port-id-two'
        host = 'fake_host'
        vif_type = portbindings.VIF_TYPE_UNBOUND
        self._setup_neutron_network(network_id)
        self._setup_neutron_port(network_id, port_id_one)
        self._setup_neutron_portbinding(port_id_one, vif_type, host)
        self._setup_neutron_port(network_id, port_id_two)
        self._setup_neutron_portbinding(port_id_two, vif_type, host)

        port_host = ml2_db.get_port_binding_host(port_id)
        self.assertIsNone(port_host)

    def test_get_port_binding_host_result_not_found(self):
        port_id = uuidutils.generate_uuid()

        port_host = ml2_db.get_port_binding_host(port_id)
        self.assertIsNone(port_host)

    def test_get_port(self):
        network_id = 'foo-network-id'
        port_id = 'foo-port-id'
        self._setup_neutron_network(network_id)
        self._setup_neutron_port(network_id, port_id)

        port = ml2_db.get_port(self.ctx.session, port_id)
        self.assertEqual(port_id, port.id)

    def test_get_port_multiple_results_found(self):
        network_id = 'foo-network-id'
        port_id = 'foo-port-id'
        port_id_one = 'foo-port-id-one'
        port_id_two = 'foo-port-id-two'
        self._setup_neutron_network(network_id)
        self._setup_neutron_port(network_id, port_id_one)
        self._setup_neutron_port(network_id, port_id_two)

        port = ml2_db.get_port(self.ctx.session, port_id)
        self.assertIsNone(port)

    def test_get_port_result_not_found(self):
        port_id = uuidutils.generate_uuid()
        port = ml2_db.get_port(self.ctx.session, port_id)
        self.assertIsNone(port)

    def test_get_port_from_device_mac(self):
        network_id = 'foo-network-id'
        port_id = 'foo-port-id'
        mac_address = 'foo_mac_address'
        self._setup_neutron_network(network_id)
        self._setup_neutron_port(network_id, port_id)

        port = ml2_db.get_port_from_device_mac(mac_address)
        self.assertEqual(port_id, port.id)

    def test_get_locked_port_and_binding(self):
        network_id = 'foo-network-id'
        port_id = 'foo-port-id'
        host = 'fake_host'
        vif_type = portbindings.VIF_TYPE_UNBOUND
        self._setup_neutron_network(network_id)
        self._setup_neutron_port(network_id, port_id)
        self._setup_neutron_portbinding(port_id, vif_type, host)

        port, binding = ml2_db.get_locked_port_and_binding(self.ctx.session,
                                                           port_id)
        self.assertEqual(port_id, port.id)
        self.assertEqual(port_id, binding.port_id)

    def test_get_locked_port_and_binding_result_not_found(self):
        port_id = uuidutils.generate_uuid()

        port, binding = ml2_db.get_locked_port_and_binding(self.ctx.session,
                                                           port_id)
        self.assertIsNone(port)
        self.assertIsNone(binding)
