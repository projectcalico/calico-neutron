# Copyright 2012 OpenStack Foundation
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

import os
import sys

import eventlet
eventlet.monkey_patch()

import netaddr
from oslo.config import cfg

from neutron.agent.common import config
from neutron.agent.linux import dhcp
from neutron.agent.linux import external_process
from neutron.agent.linux import interface
from neutron.agent.linux import ovs_lib  # noqa
from neutron.agent import rpc as agent_rpc
from neutron.common import config as common_config
from neutron.common import constants
from neutron.common import exceptions
from neutron.common import rpc as n_rpc
from neutron.common import topics
from neutron.common import utils
from neutron import context
from neutron import manager
from neutron.openstack.common import importutils
from neutron.openstack.common import log as logging
from neutron.openstack.common import loopingcall
from neutron.openstack.common import service
from neutron import service as neutron_service

LOG = logging.getLogger(__name__)


class DhcpAgent(manager.Manager):
    """
    DHCP agent.  Manages a DHCP driver (such as the dnsmasq wrapper).

    Architecture:

    - Receives RPC messages for networks, subnet and port CRUD
      operations.
    - To avoid blocking the RPC queue while handling the messages,
      queues all updates to a worker thread.
    - The worker thread processes messages in turn, coalescing
      port updates into single calls to the driver's
      reload_allocations method.

    """
    OPTS = [
        cfg.IntOpt('resync_interval', default=5,
                   help=_("Interval to resync.")),
        cfg.StrOpt('dhcp_driver',
                   default='neutron.agent.linux.dhcp.Dnsmasq',
                   help=_("The driver used to manage the DHCP server.")),
        cfg.BoolOpt('enable_isolated_metadata', default=False,
                    help=_("Support Metadata requests on isolated networks.")),
        cfg.BoolOpt('enable_metadata_network', default=False,
                    help=_("Allows for serving metadata requests from a "
                           "dedicated network. Requires "
                           "enable_isolated_metadata = True")),
        cfg.IntOpt('num_sync_threads', default=4,
                   help=_('Number of threads to use during sync process.')),
        cfg.StrOpt('metadata_proxy_socket',
                   default='$state_path/metadata_proxy',
                   help=_('Location of Metadata Proxy UNIX domain '
                          'socket')),
    ]

    def __init__(self, host=None):
        super(DhcpAgent, self).__init__(host=host)
        self.needs_resync_reasons = []
        self.conf = cfg.CONF
        self.cache = NetworkCache()
        """Cache of the current state of the networks, owned by the
        worker thread."""
        self.root_helper = config.get_root_helper(self.conf)
        self.dhcp_driver_cls = importutils.import_class(self.conf.dhcp_driver)

        self.queue = eventlet.queue.Queue()
        """Queue used to send messages to our worker thread."""
        self.dirty_networks = set()
        """
        Set of networks that need to be refreshed via a call to
        the driver's reload_allocations method.
        """

        # Work out if DHCP serving for bridged or routed VM interfaces.
        try:
            interface_driver = importutils.import_object(
                self.conf.interface_driver, self.conf)
            self.bridged = interface_driver.bridged()
        except Exception as e:
            msg = (_("Error importing interface driver '%(driver)s': "
                   "%(inner)s") % {'driver': self.conf.interface_driver,
                                   'inner': e})
            LOG.error(msg)
            raise SystemExit(msg)

        ctx = context.get_admin_context_without_session()
        self.plugin_rpc = DhcpPluginApi(topics.PLUGIN,
                                        ctx,
                                        self.bridged and
                                        self.conf.use_namespaces)
        # create dhcp dir to store dhcp info
        dhcp_dir = os.path.dirname("/%s/dhcp/" % self.conf.state_path)
        if not os.path.isdir(dhcp_dir):
            os.makedirs(dhcp_dir, 0o755)
        self.dhcp_version = self.dhcp_driver_cls.check_version()
        self._populate_networks_cache()

    def _populate_networks_cache(self):
        """Populate the networks cache when the DHCP-agent starts."""
        try:
            existing_networks = self.dhcp_driver_cls.existing_dhcp_networks(
                self.conf,
                self.root_helper
            )
            for net_id in existing_networks:
                net = dhcp.NetModel(self.bridged and
                                    self.conf.use_namespaces,
                                    {"id": net_id,
                                     "subnets": [],
                                     "ports": []})
                self.cache.put(net)
        except NotImplementedError:
            # just go ahead with an empty networks cache
            LOG.debug(
                _("The '%s' DHCP-driver does not support retrieving of a "
                  "list of existing networks"),
                self.conf.dhcp_driver
            )

    def after_start(self):
        self.run()
        LOG.info(_("DHCP agent started"))

    def run(self):
        """
        Starts the worker thread, which owns the driver and does our
        periodic resyncs.
        """
        eventlet.spawn(self._loop)

    def _loop(self):
        """
        Worker loop, owns the driver and cache.
        """
        self.sync_state()

        while True:
            if self.needs_resync_reasons:
                # be careful to avoid a race with additions to list
                # from other threads
                reasons = self.needs_resync_reasons
                self.needs_resync_reasons = []
                for r in reasons:
                    LOG.debug(_("resync: %(reason)s"), {"reason": r})
                self.sync_state()
            try:
                # Wait for messages.  Wake up at least every resync interval
                # to check for any need to resync.
                batch = [self.queue.get(timeout=self.conf.resync_interval)]
            except eventlet.queue.Empty:
                continue
            else:
                # Opportunistically grab as many messages as we can from the
                # queue.  This allows us to coalesce multiple port
                # update/delete messages below.  Since we don't yield here,
                # we also can't build up an unlimited batch.
                while not self.queue.empty():
                    batch.append(self.queue.get())

                while batch:
                    msg_hndlr, params = batch.pop(0)
                    if (self.dirty_networks and
                            (msg_hndlr not in (self._handle_port_delete,
                                               self._handle_port_update))):
                        # This isn't a message that we can coalesce, process
                        # any dirty networks now before we handle the message
                        # itself.
                        self._reload_dirty_networks()
                    msg_hndlr(**params)
                if self.dirty_networks:
                    self._reload_dirty_networks()

    @utils.synchronized('dhcp-agent')
    def _reload_dirty_networks(self):
        """
        Calls reload_allocations for any networks marked as dirty.

        Clears the dirty_networks set.
        """
        for network_id in self.dirty_networks:
            network = self.cache.get_network_by_id(network_id)
            self.call_driver('reload_allocations', network)
        self.dirty_networks.clear()

    def call_driver(self, action, network, **action_kwargs):
        """Invoke an action on a DHCP driver instance."""
        LOG.debug(_('Calling driver for network: %(net)s action: %(action)s'),
                  {'net': network.id, 'action': action})
        try:
            # the Driver expects something that is duck typed similar to
            # the base models.
            driver = self.dhcp_driver_cls(self.conf,
                                          network,
                                          self.root_helper,
                                          self.dhcp_version,
                                          self.plugin_rpc)

            getattr(driver, action)(**action_kwargs)
            return True
        except exceptions.Conflict:
            # No need to resync here, the agent will receive the event related
            # to a status update for the network
            LOG.warning(_('Unable to %(action)s dhcp for %(net_id)s: there is '
                          'a conflict with its current state; please check '
                          'that the network and/or its subnet(s) still exist.')
                        % {'net_id': network.id, 'action': action})
        except Exception as e:
            self.schedule_resync(e)
            if (isinstance(e, n_rpc.RemoteError)
                and e.exc_type == 'NetworkNotFound'
                or isinstance(e, exceptions.NetworkNotFound)):
                LOG.warning(_("Network %s has been deleted."), network.id)
            else:
                LOG.exception(_('Unable to %(action)s dhcp for %(net_id)s.')
                              % {'net_id': network.id, 'action': action})

    def schedule_resync(self, reason):
        """Schedule a resync for a given reason."""
        self.needs_resync_reasons.append(reason)

    @utils.synchronized('dhcp-agent')
    def sync_state(self):
        """Sync the local DHCP state with Neutron."""
        LOG.info(_('Synchronizing state'))
        pool = eventlet.GreenPool(cfg.CONF.num_sync_threads)
        known_network_ids = set(self.cache.get_network_ids())

        try:
            active_networks = self.plugin_rpc.get_active_networks_info()
            active_network_ids = set(network.id for network in active_networks)
            for deleted_id in known_network_ids - active_network_ids:
                try:
                    self.disable_dhcp_helper(deleted_id)
                except Exception as e:
                    self.schedule_resync(e)
                    LOG.exception(_('Unable to sync network state on deleted '
                                    'network %s'), deleted_id)

            for network in active_networks:
                pool.spawn(self.safe_configure_dhcp_for_network, network)
            pool.waitall()
            LOG.info(_('Synchronizing state complete'))

        except Exception as e:
            self.schedule_resync(e)
            LOG.exception(_('Unable to sync network state.'))

    def safe_get_network_info(self, network_id):
        try:
            network = self.plugin_rpc.get_network_info(network_id)
            if not network:
                LOG.warn(_('Network %s has been deleted.'), network_id)
            return network
        except Exception as e:
            self.schedule_resync(e)
            LOG.exception(_('Network %s info call failed.'), network_id)

    def enable_dhcp_helper(self, network_id):
        """Enable DHCP for a network that meets enabling criteria."""
        network = self.safe_get_network_info(network_id)
        if network:
            self.configure_dhcp_for_network(network)

    @utils.exception_logger()
    def safe_configure_dhcp_for_network(self, network):
        try:
            self.configure_dhcp_for_network(network)
        except (exceptions.NetworkNotFound, RuntimeError):
            LOG.warn(_('Network %s may have been deleted and its resources '
                       'may have already been disposed.'), network.id)

    def configure_dhcp_for_network(self, network):
        if not network.admin_state_up:
            return

        enable_metadata = self.dhcp_driver_cls.should_enable_metadata(
                self.conf, network)
        dhcp_network_enabled = False

        for subnet in network.subnets:
            if subnet.enable_dhcp:
                if self.call_driver('enable', network):
                    dhcp_network_enabled = True
                    self.cache.put(network)
                break

        if self.bridged and enable_metadata and dhcp_network_enabled:
            for subnet in network.subnets:
                if subnet.ip_version == 4 and subnet.enable_dhcp:
                    self.enable_isolated_metadata_proxy(network)
                    break

    def disable_dhcp_helper(self, network_id):
        """Disable DHCP for a network known to the agent."""
        network = self.cache.get_network_by_id(network_id)
        if network:
            if (self.bridged and
                self.conf.use_namespaces and
                self.conf.enable_isolated_metadata):
                # NOTE(jschwarz): In the case where a network is deleted, all
                # the subnets and ports are deleted before this function is
                # called, so checking if 'should_enable_metadata' is True
                # for any subnet is false logic here.
                self.disable_isolated_metadata_proxy(network)
            if self.call_driver('disable', network):
                self.cache.remove(network)

    def refresh_dhcp_helper(self, network_id):
        """Refresh or disable DHCP for a network depending on the current state
        of the network.
        """
        old_network = self.cache.get_network_by_id(network_id)
        if not old_network:
            # DHCP current not running for network.
            return self.enable_dhcp_helper(network_id)

        network = self.safe_get_network_info(network_id)
        if not network:
            return

        old_cidrs = set(s.cidr for s in old_network.subnets if s.enable_dhcp)
        new_cidrs = set(s.cidr for s in network.subnets if s.enable_dhcp)

        if new_cidrs and old_cidrs == new_cidrs:
            self.call_driver('reload_allocations', network)
            self.cache.put(network)
        elif new_cidrs:
            if self.call_driver('restart', network):
                self.cache.put(network)
        else:
            self.disable_dhcp_helper(network.id)

    def network_create_end(self, context, payload):
        """
        Handle the network.create.end notification event.

        Parses the message and then queues the operation.
        """
        network_id = payload['network']['id']
        LOG.info("Network created: %s", network_id)
        self.queue.put((self._handle_network_create,
                         {"network_id": network_id}))

    @utils.synchronized('dhcp-agent')
    def _handle_network_create(self, network_id):
        LOG.debug("Worker: Handling network create for %s.", network_id)
        self.enable_dhcp_helper(network_id)

    def network_update_end(self, context, payload):
        """
        Handle the network.update.end notification event.

        Parses the message and then queues the operation.
        """
        network_id = payload['network']['id']
        up = payload['network']['admin_state_up']
        LOG.info("Network updated: %s. Up? %s", network_id, up)
        self.queue.put((self._handle_network_update, {"network_id": network_id,
                                                  "up": up}))

    @utils.synchronized('dhcp-agent')
    def _handle_network_update(self, network_id, up):
        LOG.debug("Worker: Handling network update for %s: %s", network_id, up)
        if up:
            self.enable_dhcp_helper(network_id)
        else:
            self.disable_dhcp_helper(network_id)

    def network_delete_end(self, context, payload):
        """
        Handle the network.delete.end notification event.

        Parses the message and then queues the operation.
        """
        network_id = payload['network_id']
        LOG.info("Network deleted: %s. Up? %s", network_id)
        self.queue.put((self._handle_network_delete,
                         {"network_id": network_id}))

    @utils.synchronized('dhcp-agent')
    def _handle_network_delete(self, network_id):
        LOG.debug("Worker: Handling network deletion for %s", network_id)
        self.disable_dhcp_helper(network_id)

    def subnet_update_end(self, context, payload):
        """
        Handle the subnet.update.end notification event.

        Parses the message and then queues the operation.
        """
        network_id = payload['subnet']['network_id']
        LOG.info("Subnet updated, network %s", network_id)
        self.queue.put((self._handle_subnet_update, {"network_id": network_id}))

    @utils.synchronized('dhcp-agent')
    def _handle_subnet_update(self, network_id):
        LOG.debug("Worker: Handling subnet update for %s", network_id)
        self.refresh_dhcp_helper(network_id)

    # Use the update handler for the subnet create event.
    subnet_create_end = subnet_update_end

    def subnet_delete_end(self, context, payload):
        """
        Handle the subnet.delete.end notification event.

        Parses the message and then queues the operation.
        """
        subnet_id = payload['subnet_id']
        LOG.info("Subnet deleted %s", subnet_id)
        self.queue.put((self._handle_subnet_delete, {"subnet_id": subnet_id}))

    @utils.synchronized('dhcp-agent')
    def _handle_subnet_delete(self, subnet_id):
        LOG.debug("Worker: Handling subnet delete for %s", subnet_id)
        network = self.cache.get_network_by_subnet_id(subnet_id)
        if network:
            LOG.debug("Network found, refreshing dhcp helper.")
            self.refresh_dhcp_helper(network.id)

    def port_update_end(self, context, payload):
        """
        Handle the port.update.end notification event.

        Parses the message and then queues the operation.
        """
        updated_port = dhcp.DictModel(payload['port'])
        LOG.info("Port updated: %s", updated_port.id)
        self.queue.put((self._handle_port_update, {"updated_port": updated_port}))

    def _handle_port_update(self, updated_port):
        LOG.debug("Worker: Handling port update for %s", updated_port.id)
        network = self.cache.get_network_by_id(updated_port.network_id)
        if network:
            LOG.debug("Network for port found, updating cache/driver.")
            self.cache.put_port(updated_port)
            self.dirty_networks.add(updated_port.network_id)

    # Use the update handler for the port create event.
    port_create_end = port_update_end

    def port_delete_end(self, context, payload):
        """
        Handle the port.delete.end notification event.

        Parses the message and then queues the operation.
        """
        port_id = payload['port_id']
        LOG.info("Port deleted: %s", port_id)
        self.queue.put((self._handle_port_delete, {"port_id": port_id}))

    def _handle_port_delete(self, port_id):
        LOG.debug("Worker: Handling port deletion for %s", port_id)
        port = self.cache.get_port_by_id(port_id)
        if port:
            LOG.debug("Port %s found, updating cache/driver.", port_id)
            self.cache.remove_port(port)
            network = self.cache.get_network_by_id(port.network_id)
            self.dirty_networks.add(port.network_id)

    def enable_isolated_metadata_proxy(self, network):

        # The proxy might work for either a single network
        # or all the networks connected via a router
        # to the one passed as a parameter
        neutron_lookup_param = '--network_id=%s' % network.id
        meta_cidr = netaddr.IPNetwork(dhcp.METADATA_DEFAULT_CIDR)
        has_metadata_subnet = any(netaddr.IPNetwork(s.cidr) in meta_cidr
                                  for s in network.subnets)
        if (self.conf.enable_metadata_network and has_metadata_subnet):
            router_ports = [port for port in network.ports
                            if (port.device_owner ==
                                constants.DEVICE_OWNER_ROUTER_INTF)]
            if router_ports:
                # Multiple router ports should not be allowed
                if len(router_ports) > 1:
                    LOG.warning(_("%(port_num)d router ports found on the "
                                  "metadata access network. Only the port "
                                  "%(port_id)s, for router %(router_id)s "
                                  "will be considered"),
                                {'port_num': len(router_ports),
                                 'port_id': router_ports[0].id,
                                 'router_id': router_ports[0].device_id})
                neutron_lookup_param = ('--router_id=%s' %
                                        router_ports[0].device_id)

        def callback(pid_file):
            metadata_proxy_socket = cfg.CONF.metadata_proxy_socket
            proxy_cmd = ['neutron-ns-metadata-proxy',
                         '--pid_file=%s' % pid_file,
                         '--metadata_proxy_socket=%s' % metadata_proxy_socket,
                         neutron_lookup_param,
                         '--state_path=%s' % self.conf.state_path,
                         '--metadata_port=%d' % dhcp.METADATA_PORT]
            proxy_cmd.extend(config.get_log_args(
                cfg.CONF, 'neutron-ns-metadata-proxy-%s.log' % network.id))
            return proxy_cmd

        pm = external_process.ProcessManager(
            self.conf,
            network.id,
            self.root_helper,
            network.namespace)
        pm.enable(callback)

    def disable_isolated_metadata_proxy(self, network):
        pm = external_process.ProcessManager(
            self.conf,
            network.id,
            self.root_helper,
            network.namespace)
        pm.disable()


class DhcpPluginApi(n_rpc.RpcProxy):
    """Agent side of the dhcp rpc API.

    API version history:
        1.0 - Initial version.
        1.1 - Added get_active_networks_info, create_dhcp_port,
              and update_dhcp_port methods.

    """

    BASE_RPC_API_VERSION = '1.1'

    def __init__(self, topic, context, use_namespaces):
        super(DhcpPluginApi, self).__init__(
            topic=topic, default_version=self.BASE_RPC_API_VERSION)
        self.context = context
        self.host = cfg.CONF.host
        self.use_namespaces = use_namespaces

    def get_active_networks_info(self):
        """Make a remote process call to retrieve all network info."""
        networks = self.call(self.context,
                             self.make_msg('get_active_networks_info',
                                           host=self.host))
        return [dhcp.NetModel(self.use_namespaces, n) for n in networks]

    def get_network_info(self, network_id):
        """Make a remote process call to retrieve network info."""
        network = self.call(self.context,
                            self.make_msg('get_network_info',
                                          network_id=network_id,
                                          host=self.host))
        if network:
            return dhcp.NetModel(self.use_namespaces, network)

    def get_dhcp_port(self, network_id, device_id):
        """Make a remote process call to get the dhcp port."""
        port = self.call(self.context,
                         self.make_msg('get_dhcp_port',
                                       network_id=network_id,
                                       device_id=device_id,
                                       host=self.host))
        if port:
            return dhcp.DictModel(port)

    def create_dhcp_port(self, port):
        """Make a remote process call to create the dhcp port."""
        port = self.call(self.context,
                         self.make_msg('create_dhcp_port',
                                       port=port,
                                       host=self.host))
        if port:
            return dhcp.DictModel(port)

    def update_dhcp_port(self, port_id, port):
        """Make a remote process call to update the dhcp port."""
        port = self.call(self.context,
                         self.make_msg('update_dhcp_port',
                                       port_id=port_id,
                                       port=port,
                                       host=self.host))
        if port:
            return dhcp.DictModel(port)

    def release_dhcp_port(self, network_id, device_id):
        """Make a remote process call to release the dhcp port."""
        return self.call(self.context,
                         self.make_msg('release_dhcp_port',
                                       network_id=network_id,
                                       device_id=device_id,
                                       host=self.host))

    def release_port_fixed_ip(self, network_id, device_id, subnet_id):
        """Make a remote process call to release a fixed_ip on the port."""
        return self.call(self.context,
                         self.make_msg('release_port_fixed_ip',
                                       network_id=network_id,
                                       subnet_id=subnet_id,
                                       device_id=device_id,
                                       host=self.host))


class NetworkCache(object):
    """Agent cache of the current network state."""
    def __init__(self):
        self.cache = {}
        self.subnet_lookup = {}
        self.port_lookup = {}

    def get_network_ids(self):
        return self.cache.keys()

    def get_network_by_id(self, network_id):
        return self.cache.get(network_id)

    def get_network_by_subnet_id(self, subnet_id):
        return self.cache.get(self.subnet_lookup.get(subnet_id))

    def get_network_by_port_id(self, port_id):
        return self.cache.get(self.port_lookup.get(port_id))

    def put(self, network):
        if network.id in self.cache:
            self.remove(self.cache[network.id])

        self.cache[network.id] = network

        for subnet in network.subnets:
            self.subnet_lookup[subnet.id] = network.id

        for port in network.ports:
            self.port_lookup[port.id] = network.id

    def remove(self, network):
        del self.cache[network.id]

        for subnet in network.subnets:
            del self.subnet_lookup[subnet.id]

        for port in network.ports:
            del self.port_lookup[port.id]

    def put_port(self, port):
        network = self.get_network_by_id(port.network_id)
        for index in range(len(network.ports)):
            if network.ports[index].id == port.id:
                network.ports[index] = port
                break
        else:
            network.ports.append(port)

        self.port_lookup[port.id] = network.id

    def remove_port(self, port):
        network = self.get_network_by_port_id(port.id)

        for index in range(len(network.ports)):
            if network.ports[index] == port:
                del network.ports[index]
                del self.port_lookup[port.id]
                break

    def get_port_by_id(self, port_id):
        network = self.get_network_by_port_id(port_id)
        if network:
            for port in network.ports:
                if port.id == port_id:
                    return port

    def get_state(self):
        net_ids = self.get_network_ids()
        num_nets = len(net_ids)
        num_subnets = 0
        num_ports = 0
        for net_id in net_ids:
            network = self.get_network_by_id(net_id)
            num_subnets += len(network.subnets)
            num_ports += len(network.ports)
        return {'networks': num_nets,
                'subnets': num_subnets,
                'ports': num_ports}


class DhcpAgentWithStateReport(DhcpAgent):
    def __init__(self, host=None):
        super(DhcpAgentWithStateReport, self).__init__(host=host)
        self.state_rpc = agent_rpc.PluginReportStateAPI(topics.PLUGIN)
        self.agent_state = {
            'binary': 'neutron-dhcp-agent',
            'host': host,
            'topic': topics.DHCP_AGENT,
            'configurations': {
                'dhcp_driver': cfg.CONF.dhcp_driver,
                'use_namespaces': cfg.CONF.use_namespaces,
                'dhcp_lease_duration': cfg.CONF.dhcp_lease_duration},
            'start_flag': True,
            'agent_type': constants.AGENT_TYPE_DHCP}
        report_interval = cfg.CONF.AGENT.report_interval
        self.use_call = True
        if report_interval:
            self.heartbeat = loopingcall.FixedIntervalLoopingCall(
                self._report_state)
            self.heartbeat.start(interval=report_interval)

    def _report_state(self):
        try:
            self.agent_state.get('configurations').update(
                self.cache.get_state())
            ctx = context.get_admin_context_without_session()
            self.state_rpc.report_state(ctx, self.agent_state, self.use_call)
            self.use_call = False
        except AttributeError:
            # This means the server does not support report_state
            LOG.warn(_("Neutron server does not support state report."
                       " State report for this agent will be disabled."))
            self.heartbeat.stop()
            self.run()
            return
        except Exception:
            LOG.exception(_("Failed reporting state!"))
            return
        if self.agent_state.pop('start_flag', None):
            self.run()

    def agent_updated(self, context, payload):
        """Handle the agent_updated notification event."""
        self.schedule_resync(_("Agent updated: %(payload)s") %
                             {"payload": payload})
        LOG.info(_("agent_updated by server side %s!"), payload)

    def after_start(self):
        LOG.info(_("DHCP agent started"))


def register_options():
    cfg.CONF.register_opts(DhcpAgent.OPTS)
    config.register_interface_driver_opts_helper(cfg.CONF)
    config.register_use_namespaces_opts_helper(cfg.CONF)
    config.register_agent_state_opts_helper(cfg.CONF)
    config.register_root_helper(cfg.CONF)
    cfg.CONF.register_opts(dhcp.OPTS)
    cfg.CONF.register_opts(interface.OPTS)


def main():
    register_options()
    common_config.init(sys.argv[1:])
    config.setup_logging()
    server = neutron_service.Service.create(
        binary='neutron-dhcp-agent',
        topic=topics.DHCP_AGENT,
        report_interval=cfg.CONF.AGENT.report_interval,
        manager='neutron.agent.dhcp_agent.DhcpAgentWithStateReport')
    service.launch(server).wait()
