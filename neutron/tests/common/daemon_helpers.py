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

import os

import fixtures
from oslo_config import cfg

from neutron.agent.linux import external_process
from neutron.tests.functional.agent.linux import simple_daemon


class DaemonFixture(fixtures.Fixture):
    def __init__(self, namespace=None, uuid=None, pid_file=None):
        super(DaemonFixture, self).__init__()
        self.namespace = namespace
        self.uuid = uuid
        self.pid_file = pid_file

    def _setUp(self):
        self._child_process = None
        self._process_monitor = external_process.ProcessMonitor(
            config=cfg.CONF, resource_type='test')
        self.addCleanup(self.cleanup_spawned_child)
        self.spawn()

    def make_cmdline(self, pid_file):
        return ['python', simple_daemon.__file__,
                '--uuid=%s' % self.uuid,
                '--pid_file=%s' % pid_file]

    def spawn(self):
        pm = external_process.ProcessManager(
            conf=cfg.CONF,
            uuid=self.uuid,
            namespace=self.namespace,
            pid_file=self.pid_file,
            default_cmd_callback=self.make_cmdline)
        pm.enable()
        self._process_monitor.register(self.uuid, 'test-service', pm)
        self._child_process = pm

    def cleanup_spawned_child(self):
        if self._child_process:
            self._child_process.disable()


class DnsmasqFixture(DaemonFixture):
    def __init__(self, namespace=None, network_id=None):
        pid_file = os.path.join(
            os.path.join(cfg.CONF.dhcp_confs, network_id), 'pid')
        super(DnsmasqFixture, self).__init__(namespace, network_id, pid_file)

    def make_cmdline(self, pid_file):
        return ['dnsmasq', '--pid-file=%s' % pid_file]


class MetadataProxyFixture(DaemonFixture):
    def __init__(self, namespace=None, router_id=None):
        self.router_id = router_id
        super(MetadataProxyFixture, self).__init__(namespace, router_id)

    def make_cmdline(self, pid_file):
        return ['neutron-ns-metadata-proxy',
                '--pid_file=%s' % pid_file,
                '--router_id=%s' % self.router_id]
