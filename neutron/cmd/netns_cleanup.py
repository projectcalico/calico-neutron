# Copyright (c) 2012 OpenStack Foundation.
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

import itertools
import logging as std_logging
import os
import re
import time

from oslo_config import cfg
from oslo_log import log as logging
from oslo_utils import importutils
from oslo_utils import timeutils
import pyroute2
from pyroute2 import netns
import signal

from neutron.agent.common import config as agent_config
from neutron.agent.common import ovs_lib
from neutron.agent.dhcp import config as dhcp_config
from neutron.agent.l3 import agent as l3_agent
from neutron.agent.l3 import dvr
from neutron.agent.l3 import dvr_fip_ns
from neutron.agent.linux import dhcp
from neutron.agent.linux import external_process
from neutron.agent.linux import interface
from neutron.agent.linux import ip_lib
from neutron.api.v2 import attributes
from neutron.common import config
from neutron.i18n import _LE, _LI


LOG = logging.getLogger(__name__)

PREFIXES = {
    'l3': [l3_agent.NS_PREFIX, dvr.SNAT_NS_PREFIX, dvr_fip_ns.FIP_NS_PREFIX],
    'dhcp': [dhcp.NS_PREFIX],
}


class FakeDhcpPlugin(object):
    """Fake RPC plugin to bypass any RPC calls."""
    def __getattribute__(self, name):
        def fake_method(*args):
            pass
        return fake_method


def setup_conf():
    """Setup the cfg for the clean up utility.

    Use separate setup_conf for the utility because there are many options
    from the main config that do not apply during clean-up.
    """

    cli_opts = [
        cfg.BoolOpt('force',
                    default=False,
                    help=_('Delete the namespace by removing all devices.')),
        cfg.StrOpt('agent-type',
                   help=_('Cleanup resource for a specific agent type only.')),
        cfg.IntOpt('terminate-timeout',
                   default=15,
                   help=_('Timeout to let processes terminate gracefully.')),
        cfg.IntOpt('check-interval',
                   default=1,
                   help=_('How frequently to check process status.')),
    ]

    conf = cfg.CONF
    conf.register_cli_opts(cli_opts)
    agent_config.register_interface_driver_opts_helper(conf)
    agent_config.register_use_namespaces_opts_helper(conf)
    conf.register_opts(dhcp_config.DHCP_AGENT_OPTS)
    conf.register_opts(dhcp_config.DHCP_OPTS)
    conf.register_opts(dhcp_config.DNSMASQ_OPTS)
    conf.register_opts(interface.OPTS)
    return conf


def _get_dhcp_process_monitor(config):
    return external_process.ProcessMonitor(config=config,
                                           resource_type='dhcp')


def kill_dhcp(conf, namespace):
    """Disable DHCP for a network if DHCP is still active."""
    network_id = namespace.replace(dhcp.NS_PREFIX, '')

    dhcp_driver = importutils.import_object(
        conf.dhcp_driver,
        conf=conf,
        process_monitor=_get_dhcp_process_monitor(conf),
        network=dhcp.NetModel(conf.use_namespaces, {'id': network_id}),
        plugin=FakeDhcpPlugin())

    if dhcp_driver.active:
        dhcp_driver.disable()


def kill_processes(namespace):
    ip_wrapper = ip_lib.IPWrapper(namespace=namespace)

    pids = ip_wrapper.netns.pids(namespace)
    if pids:
        for pid in pids:
            cmd = ['kill', '-9'] + [pid]
            ip_wrapper.netns.execute(cmd)


def eligible_for_deletion(conf, namespace, force=False):
    """Determine whether a namespace is eligible for deletion.

    Eligibility is determined by having only the lo device or if force
    is passed as a parameter.
    """

    prefixes = None
    if conf.agent_type:
        prefixes = PREFIXES.get(conf.agent_type)

    if not prefixes:
        prefixes = itertools.chain(*PREFIXES.values())
    ns_mangling_pattern = '(%s%s)' % ('|'.join(prefixes),
                                      attributes.UUID_PATTERN)

    # filter out namespaces without UUID as the name
    if not re.match(ns_mangling_pattern, namespace):
        return False

    ip = ip_lib.IPWrapper(namespace=namespace)
    return force or ip.namespace_is_empty()


def unplug_device(conf, device):
    try:
        device.link.delete()
    except RuntimeError:
        # Maybe the device is OVS port, so try to delete
        ovs = ovs_lib.BaseOVS()
        bridge_name = ovs.get_bridge_for_iface(device.name)
        if bridge_name:
            bridge = ovs_lib.OVSBridge(bridge_name)
            bridge.delete_port(device.name)
        else:
            LOG.debug('Unable to find bridge for device: %s', device.name)


def destroy_namespace(conf, namespace, force=False):
    """Destroy a given namespace.

    If force is True, then dhcp (if it exists) will be disabled and all
    devices will be forcibly removed.
    """

    try:
        ip = ip_lib.IPWrapper(namespace=namespace)

        if force:
            kill_processes(namespace)

            for device in ip.get_devices(exclude_loopback=True):
                unplug_device(conf, device)

        ip.garbage_collect_namespace()
    except Exception:
        LOG.exception(_LE('Error unable to destroy namespace: %s'), namespace)


def cleanup_network_namespaces(conf):
    # Identify namespaces that are candidates for deletion.
    candidates = [ns for ns in
                  ip_lib.IPWrapper.get_namespaces()
                  if eligible_for_deletion(conf, ns, conf.force)]

    if candidates:
        time.sleep(2)

        for namespace in candidates:
            destroy_namespace(conf, namespace, conf.force)


def get_all_pids():
    return set(int(f) for f in os.listdir('/proc') if f.isdigit())


def get_netns_pids(namespaces):
    """Get set of pids in the given list of namespaces.
    The code is based on Linux iproute2 utility
    (http://git.kernel.org/cgit/linux/kernel/git/shemminger/iproute2.git/tree/
    ip/ipnetns.c?id=v3.16.0#n236)
    """
    ns_stats = set()
    for namespace in namespaces:
        try:
            ns_stat = os.stat('/var/run/netns/%s' % namespace)
            ns_stats.add((ns_stat.st_dev, ns_stat.st_ino))
        except OSError as e:
            LOG.error(_LE('Could not get stat for namespace: %s'), e)

    result = set()

    for pid in get_all_pids():
        try:
            pid_stat = os.stat('/proc/%d/ns/net' % pid)
            st_dev = pid_stat.st_dev
            st_ino = pid_stat.st_ino
            if (st_dev, st_ino) in ns_stats:
                result.add(pid)
        except OSError as e:
            LOG.error(_LE('Could not get stat for pid: %s'), e)

    return result


def batch_kill_processes(namespaces, terminate_timeout, check_interval):
    pids = get_netns_pids(namespaces)

    if not pids:
        return

    watch = timeutils.StopWatch(terminate_timeout)
    watch.start()

    # send SIGTERM to all pids
    dead_pids = set()
    wait_watch = timeutils.StopWatch()
    wait_watch.start()

    for pid in pids:
        try:
            LOG.debug('Terminating process: %s', pid)
            os.kill(pid, signal.SIGTERM)
        except OSError as e:
            LOG.error(_LE('Could not send SIGTERM to pid: %s'), e)
            dead_pids.add(pid)

    pids = pids - dead_pids  # ignore those we failed send signal to

    # wait for pids to die
    while pids and not watch.expired():
        # sleep
        time_to_sleep = check_interval - wait_watch.elapsed()
        if time_to_sleep > 0:
            LOG.debug('Sleeping for %s sec', time_to_sleep)
            time.sleep(time_to_sleep)

        wait_watch.restart()
        pids = pids & get_all_pids()  # alive pids
        LOG.debug('Some pids are still alive: %s', pids)

    # kill brutally
    for pid in pids:
        LOG.debug('Killing process: %s', pid)
        try:
            os.kill(pid, signal.SIGKILL)
        except OSError:
            pass  # ignore


def fast_unplug_device(ns, link):
    name = link.get_attr('IFLA_IFNAME')
    if name == ip_lib.LOOPBACK_DEVNAME:
        return

    # delete link
    LOG.info(_LI('Delete link: %s'), name)
    try:
        ns.link_remove(link['index'])
    except pyroute2.netlink.NetlinkError:
        # unplug from OVS
        ovs = ovs_lib.BaseOVS()
        bridge_name = ovs.get_bridge_for_iface(name)
        if bridge_name:
            bridge = ovs_lib.OVSBridge(bridge_name)
            bridge.delete_port(name)


def fast_destroy_namespace(namespace, force):
    LOG.info(_LI('Processing namespace: %s'), namespace)

    ns = netns.NetNS(namespace)
    links = ns.get_links()

    if force:
        for link in links:
            fast_unplug_device(ns, link)

    ns.close()
    if force or not links:
        netns.remove(namespace)


def fast_cleanup(conf):
    candidates = [ns for ns in pyroute2.netns.listnetns()
                  if eligible_for_deletion(conf, ns, conf.force)]

    if conf.force:
        batch_kill_processes(candidates, conf.terminate_timeout,
                             conf.check_interval)

    for namespace in candidates:
        fast_destroy_namespace(namespace, conf.force)


def cleanup(conf):
    if os.geteuid() == 0:  # faster path for privileged user
        fast_cleanup(conf)
    else:
        cleanup_network_namespaces(conf)


def main():
    """Main method for cleaning up network namespaces.

    This method will make two passes checking for namespaces to delete. The
    process will identify candidates, sleep, and call garbage collect. The
    garbage collection will re-verify that the namespace meets the criteria for
    deletion (ie it is empty). The period of sleep and the 2nd pass allow
    time for the namespace state to settle, so that the check prior deletion
    will re-confirm the namespace is empty.

    The utility is designed to clean-up after the forced or unexpected
    termination of Neutron agents.

    The --force flag should only be used as part of the cleanup of a devstack
    installation as it will blindly purge namespaces and their devices. This
    option also kills any lingering DHCP instances.
    """
    conf = setup_conf()
    conf()
    config.setup_logging()
    conf.log_opt_values(LOG, std_logging.DEBUG)

    cleanup(conf)
