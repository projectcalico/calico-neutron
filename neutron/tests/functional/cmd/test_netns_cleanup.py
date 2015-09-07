# Copyright (c) 2015 Red Hat, Inc.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import mock

from neutron.agent.l3 import agent as l3_agent
from neutron.agent.linux import dhcp
from neutron.agent.linux import ip_lib
from neutron.agent.linux import utils as agent_utils
from neutron.cmd import netns_cleanup
from neutron.tests.common import daemon_helpers
from neutron.tests.common import net_helpers
from neutron.tests.functional import base

GET_NAMESPACES = 'neutron.agent.linux.ip_lib.IPWrapper.get_namespaces'
TEST_INTERFACE_DRIVER = 'neutron.agent.linux.interface.OVSInterfaceDriver'


class NetnsCleanupTest(base.BaseSudoTestCase):
    def setUp(self):
        super(NetnsCleanupTest, self).setUp()

        self.get_namespaces_p = mock.patch(GET_NAMESPACES)
        self.get_namespaces = self.get_namespaces_p.start()

    def setup_config(self, args=None):
        if args is None:
            args = []
        # force option enabled to make sure non-empty namespaces are
        # cleaned up and deleted
        args.append('--force')

        self.conf = netns_cleanup.setup_conf()
        self.conf.set_override('interface_driver', TEST_INTERFACE_DRIVER)
        self.config_parse(conf=self.conf, args=args)

    def test_cleanup_network_namespaces_cleans_dhcp_and_l3_namespaces(self):
        br_int = self.useFixture(net_helpers.OVSBridgeFixture()).bridge
        self.conf.set_override('ovs_integration_bridge', br_int.br_name)

        dhcp_namespace = self.useFixture(
            net_helpers.NamespaceFixture(dhcp.NS_PREFIX)).name

        # start dhcp process
        network_id = dhcp_namespace.replace(dhcp.NS_PREFIX, '')
        dhcp_process = self.useFixture(daemon_helpers.DnsmasqFixture(
            dhcp_namespace, network_id=network_id))

        # make sure the daemon is really started
        agent_utils.wait_until_true(lambda: dhcp_process._child_process.active)

        l3_namespace = self.useFixture(
            net_helpers.NamespaceFixture(l3_agent.NS_PREFIX)).name

        # start l3 process
        router_id = l3_namespace.replace(l3_agent.NS_PREFIX, '')
        l3_process = self.useFixture(daemon_helpers.MetadataProxyFixture(
            l3_namespace, router_id=router_id))

        # make sure the daemon is really started
        agent_utils.wait_until_true(lambda: l3_process._child_process.active)

        bridge = self.useFixture(
            net_helpers.VethPortFixture(namespace=dhcp_namespace)).bridge
        self.useFixture(
            net_helpers.VethPortFixture(bridge, l3_namespace))

        # we scope the get_namespaces to our own ones not to affect other
        # tests, as otherwise cleanup will kill them all
        self.get_namespaces.return_value = [l3_namespace, dhcp_namespace]

        netns_cleanup.cleanup(self.conf)

        self.get_namespaces_p.stop()
        namespaces_now = ip_lib.IPWrapper.get_namespaces()
        self.assertNotIn(l3_namespace, namespaces_now)
        self.assertNotIn(dhcp_namespace, namespaces_now)
        agent_utils.wait_until_true(
            lambda: not dhcp_process._child_process.active)
        agent_utils.wait_until_true(
            lambda: not l3_process._child_process.active)
