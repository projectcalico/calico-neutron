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

import mock
from oslo_db import exception as db_exc

from neutron.common import exceptions
from neutron import context
from neutron import manager
from neutron.plugins.common import constants as plugin_constants
from neutron.tests.unit.db import test_db_base_plugin_v2
from neutron.tests.unit.extensions import test_l3


class L3DBTestCase(test_db_base_plugin_v2.NeutronDbPluginV2TestCase,
                   test_l3.L3NatTestCaseMixin):

    def setUp(self):
        core_plugin = 'neutron.plugins.ml2.plugin.Ml2Plugin'
        l3_plugin = ('neutron.tests.unit.extensions.test_l3.'
                     'TestL3NatServicePlugin')
        service_plugins = {'l3_plugin_name': l3_plugin}
        ext_mgr = test_l3.L3TestExtensionManager()
        super(L3DBTestCase, self).setUp(plugin=core_plugin,
                                        service_plugins=service_plugins,
                                        ext_mgr=ext_mgr)
        self.core_plugin = manager.NeutronManager.get_plugin()
        self.ctx = context.get_admin_context()
        self.setup_notification_driver()

    def test_create_router_with_ext_gateway_tolerates_deadlock(self):
        with self.network() as net_ext:
            ext_net_id = net_ext['network']['id']
            self._set_net_external(ext_net_id)
            # we need to mack _anything_ inside create_port() to emulate db
            # deadlock
            with mock.patch.object(
                self.core_plugin,
                '_enforce_device_owner_not_router_intf_or_device_id') as foo:
                foo.side_effect = [db_exc.DBDeadlock, None]
                ext_gw_info = {'network_id': ext_net_id}
                with self.router(external_gateway_info=ext_gw_info) as r:
                    router = r['router']
                    self.assertEqual(
                        ext_net_id,
                        router['external_gateway_info']['network_id'])

    def test_create_router_with_wrong_ext_gateway_cleanup(self):
        with self.network() as net:
            net_id = net['network']['id']
            router_dict = {'router':
                           {'name': 'test_router', 'admin_state_up': True,
                            'external_gateway_info':
                            {'network_id': net_id}}}
            plugin = manager.NeutronManager.get_service_plugins().get(
                plugin_constants.L3_ROUTER_NAT)
            # creating router with gw not in external net should fail
            self.assertRaises(exceptions.BadRequest,
                              plugin.create_router, self.ctx, router_dict)
            self.assertFalse(plugin.get_routers(self.ctx))
