================
L3-only networks
================

https://bugs.launchpad.net/neutron/+bug/1472704

This document describes and proposes a kind of Neutron 'network' whose
key connectivity semantic is that it only guarantees to provide IP
connectivity between the VMs that are attached to that network.  This
is interesting, we believe, because very many data center workloads
only *need* connectivity at IP and above, and because it allows us to
experiment with implementations of that connectivity that are perhaps
simpler and more scalable than implementations that provide L2
connectivity.

.. note:: A previous incarnation of this document was submitted as a
          Neutron devref and received a lot of useful feedback in that
          form (https://review.openstack.org/#/c/198439/).  This
          version is submitted as a proposed Neutron spec.

Problem Description
===================

For some OpenStack deployments, Neutron networking is more complex
than it needs to be, and there is an incentive to use a simpler
approach in such cases, so that the networking is easier to understand
and to debug.  A simpler approach may also be more scalable, and
deliver a faster or less CPU-greedy data plane.

Two expressions of this are the RFE from a group of large deployers at
https://bugs.launchpad.net/neutron/+bug/1458890, and Project Calico.
The large deployers' RFE is expounded in the Problem Description
section of https://review.openstack.org/#/c/225384/, so I won't repeat
that here.  Project Calico is described just below.

In both cases, the people concerned already have working
implementations of what they want; the problem is just that their
semantics are not properly described by the current Neutron API.  As
these systems currently stand, a sequence of Neutron API calls is used
to set up their networking, and the implementation *interprets* those
calls to set up its desired semantics - but those semantics are not
actually the same as what the Neutron API says for the calls that were
made.  Hence the premise of this spec is: how can we best enhance the
Neutron API and data model so that it can describe the semantics that
the large deployers and Calico want to provide?

Project Calico
--------------

Calico (http://www.projectcalico.org/) is an open source project that
aims to provide L3-only connectivity in all kinds of data center and
cloud environments.  That includes OpenStack as well as
container-based platforms such as Mesos or Kubernetes.  Calico's
implementation for OpenStack comprises:

- orchestrator-independent components at
  https://github.com/projectcalico/calico

- Neutron integration code in the 'networking-calico' Neutron stadium
  project.

Note that because Calico is an actual implementation, it includes
implementation choices that are not strictly implied by the
connectivity semantics that it is designed to provide.  It is
important to distinguish between the desired L3-only connectivity
semantics - which this document describes and proposes incorporating
into the Neutron API, and which are technically Calico-independent -
and Project Calico + networking-calico as a particular implementation
of those semantics.

Simple and uniform data paths
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Calico's mainline data paths use only IP, IP routing and iptables, so
that they are easy to understand and probe, using standard tools such
as ping, traceroute and tcpdump.

Non-mainline cases might use NAT or tunneling or additional
encapsulation, but Calico aims to minimise these cases, and for their
implementation (where needed) not to impact the simple mainline case.

VM addressing and floating IPs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To avoid NAT when it is‎n't actually needed, Calico assigns an
externally routable *fixed* IP to a VM that needs inbound
connectivity, instead of using a floating IP.  A Neutron floating IP
actually combines two ideas: inbound reachability from outside the
immediate network; and IP mobility, or the ability to have a logical
IP address that can be mapped at different times to different VMs.
Calico will still use floating IPs when mobility is required, but not
when the need is only for inbound connectivity.

When a tenant has some VMs that need inbound connectivity, and others
that don't, Calico:

- allows the tenant to specify whether each VM gets an externally
  routable IP, or an IP (e.g. RFC 1918) that is not externally
  routable

- provides reachability between both kinds of IPs

- provides outbound connectivity from both kinds of IPs.

Uniform security policy
~~~~~~~~~~~~~~~~~~~~~~~

For a VM on a Neutron non-external network, effective security policy
is a composite of the security groups that are defined on that VM's
port(s), and of whether and how the network is connected to other
networks through Neutron virtual routers.  Calico's view is that, for
deployments where the focus is on very large numbers of IP-based
endpoints, it is simpler and more uniform to define security entirely
in terms of the roles that each endpoint has, and which other IP
addresses, prefixes or roles it is able to connect to - independently
of how those IP addressed endpoints might be mapped onto particular
networks, and of how those networks are interconnected.

In other words, Calico believes that having a reliable and
comprehensible security policy is more important for many deployments
than knowing or controlling how the networks involved are connected.

Shared or overlapping IPs
~~~~~~~~~~~~~~~~~~~~~~~~~

Calico is best suited for deployments that do not require private
address spaces - e.g. to allow multiple tenants to use overlapping IP
ranges.  Support for overlapping IPs fundamentally requires stateful
NAT or some kind of encapsulation or overlay, and so conflicts with
Calico's desire for simple data paths.  Calico will support
overlapping IPs where needed (by translating private address space
IPv4 packets statelessly into IPv6, transporting them across the core
as IPv6, and then translating back to IPv4 on the destination compute
host), but it primarily targets use cases where overlapping IPs are
not needed, or only used for a small fraction of data center traffic.

Required Neutron semantics
~~~~~~~~~~~~~~~~~~~~~~~~~~

Therefore Calico requires the following Neutron semantics, beyond
those that are already well-established.

- A kind of network that supports multiple IPv4 and/or IPv6 subnets,
  and only provides L3 connectivity between the VMs that are attached
  to it; and also between those VMs and the outside world.

- A way of using OpenStack/Neutron such that security policy is a
  first-class concept, in the sense of not being contingent on other
  parts of the data model.

- Floating IPs that can map to a port on the new kind of L3-only
  network.

(The simplicity, uniformity, or whatever, of the data path is not
currently expressed on the Neutron API, and we believe that that is
correct.  It is an important practical matter for someone wanting to
understand and troubleshoot a Neutron deployment; but the Neutron API
should specify only the connectivity semantics between its ports - as
it does today for L2 networks, and as this document proposes for
L3-only networks - and not how that connectivity is implemented.)

Comparison of Calico and Large Deployer use cases
-------------------------------------------------

The 'Large Deployer' use cases are described by
https://bugs.launchpad.net/neutron/+bug/1458890 and Carl Baldwin's
"Model changes to support routed network groups" spec at
https://review.openstack.org/#/c/225384/ primarily addresses those use
cases - although it does also mention Calico as a possible additional
user of its proposed new objects.

The question then arises: isn't the Calico use case just the same as
the large deployers?  Or if not, how does it differ?

My view, presented in detail just below, is that they are indeed the
same, so far as the desired connectivity and IP addressing semantics
are concerned, and hence that this document's proposal is useful for
the large deployer use case as well.

In more detail...
~~~~~~~~~~~~~~~~~

Per https://bugs.launchpad.net/neutron/+bug/1458890, the large
deployer semantics are as follows.

#. That particular (real, physical) L2 network segments may only be
   available to a subset of all compute hosts, and that deployers do
   not want to use overlays to extend those real segments into a
   virtual L2 segment that is available everywhere.

#. That Neutron should be able to describe a L3 network that is
   composed on several such L2 segments, and support the user asking
   to launch a VM on a specified L3 network.

#. That scheduling smarts and logic will be needed to ensure that the
   compute host and underlying L2 segment that are chosen have
   available resources, including IP addressing.

Implicitly, therefore, this use case only cares about L3 connectivity
between VMs that are attached to the same L3 network.  In that respect
its desired semantics are exactly the same as proposed by this
document.

The semantics above do not require that the underlying L2 network
segments are expressed in the Neutron API and data model, and so - by
Occam's razor - I believe that they should not be.  If they *were*,
that would introduce an API-level difference between the Calico and
large deployer cases, because in Calico's implementation there is
actually a different L2 segment for each VM, and it certainly would
not be practical or elegant to require Neutron API configuration of so
many L2 segment objects.  Hence there would have to be some cases
where the L2 segments were explicit, and some implicit; but the
required connectivity semantics as currently stated do not justify
that extra complexity.

Note also that the large deployer L2 segment is *not* semantically the
same as a Neutron network - because of only being available at certain
compute hosts - and so should not be modeled as such (if it is modeled
at all).

Next up is IP addressing.  Although not stated in the bug, related
discussions have clarified further requirements, for the IP address
that is allocated to a VM:

- that it should sometimes depend on the L2 segment (or rack or pod)
  that the VM's host is attached to, e.g. be allocated from a
  segment/rack/pod-specific IP prefix

- that in other cases it should be allocated from an IP range that is
  associated with the L3 network as a whole.

It might be thought that these points require explicit modeling of L2
segments (or racks or pods) so that specific IP ranges can be
associated with those, but I think that's wrong, because these same
requirements are actually interesting for Calico - which doesn't have
L2 segments at a useful scale - too, and a better approach is to look
at using pluggable IPAM.

With Calico, even though each compute host is a router, it is still
desirable to allocate IP addresses such that the IP addresses on VMs
in a given rack/pod fall with a specific IP prefix for that rack/pod.
This is so that VM routes can be aggregated on each ToR router, and on
any fabric routers between the ToR routers.  Hence the practical
requirement - that within an L3 network, IP addressing can depend on
the chosen compute host - is the same for Calico as it is for the
large deployers case.

I plan eventually to work on this for Calico by extending and using
pluggable IPAM, and have recently proposed an Outreachy internship
idea about this at https://wiki.openstack.org/wiki/Internship_ideas.
(I've proposed this as an Outreachy idea because my priority now is
the L3-only network idea, and I expect my hands to be full for a while
with helping to implement that.)

Finally, the large deployer requirements include Nova's compute host
scheduling being aware of possible hosts' L2 segments, and whether
they have IP addresses and other resources.  Again this is potentially
interesting to Calico deployments as well.  However it also interacts
with many similar conversations about making Nova's scheduling logic
depend on more things, and I think there will need to be a unified
cross-project effort and design to address all of those similar
scheduling requirements.  Therefore I suggest that we decouple it from
the other L3 connectivity and addressing aspects above.

Proposed Change
===============

A new L3Network object is added to the Neutron API and data model.  It
can have multiple IPv4 and/or IPv6 subnets.  VMs can be attached to an
L3Network as an alternative to being attached to a Neutron network.

This spec does not yet specify every detail of L3Network's properties
and methods, but it describes what an L3Network means, and the
connectivity that it provides for its attached VMs.

The naming of things, or is it a 'network'?
-------------------------------------------

We began by referring to this new thing as a kind of 'network' for two
reasons.

- When launching a group of VMs in OpenStack, one has to specify how
  those VMs will be networked, and currently one does that by giving
  the name or ID of a Neutron (L2) network.  Once L3-only 'network's
  exist, it should also be possible to launch VMs that are networked
  by attaching them to a L3-only 'network'.  So, either the
  terminology at that point will have to change, to 'network or
  <L3-only thing>', or the new thing could also be called a network.

- Neutron tradition aside, this L3-only concept is intuitively what
  (or one of the things that) most people think of as a network.  For
  example, at my employer there is a large accumulated collection of
  personal PCs, bare metal test machines and hosted VM test and
  utility machines, all wired together somehow through bridges,
  switches and routers, which we call and think of as our internal
  company network.  In practice - with rare exceptions - we only ever
  care about IP-level connectivity between machines in this network,
  i.e. that we can ping or ssh to an IP address.

  (The exceptions are also illuminating.  They are that sometimes we
  want dynamic DHCP to operate on a particular part of the network
  that is also a L2 domain.  So, sometimes, and only for some parts of
  the overall network, we do care about the L2 connectivity.  But the
  dominant overall semantic is IP only.)

However, in Neutron tradition and current terminology, a network is
fundamentally a L2 construct.  It provides Ethernet forwarding and
broadcast semantics to the ports that are connected to it, and there
is a mature system for mapping that onto underlying real networks,
such as by using one VLAN of an underlying real network to carry the
traffic for a particular Neutron network.  Although Neutron also
provides L3 addressing, this is as an optional overlay on the L2
Neutron networks, and it is possible not to use Neutron's L3 support
at all, either by using instead some non-Neutron mechanism to assign
IP addresses to the VMs that need them, or when running workloads that
do not need IP at all.

Therefore, even though it might be intuitive outside Neutron, it may
not be practical for our proposed L3-only object to be called a
network in Neutron.  For the sake of using a consistent name, this
document will call it 'L3Network' - but it is the semantics that are
important, and I am happy to discuss and change the name independently
later.

Internal connectivity semantics
-------------------------------

An L3Network provides full (subject to security policy) IP
connectivity between the VMs that are attached to it: v4 and v6,
unicast and multicast.  It provides no L2 capability except as
required for this IP connectivity - in other words, in that there will
typically still be an Ethernet header before the IP header in each
packet, because Ethernet is still being used as the transport between
any two points in the IP network - plus whatever is needed for correct
operation of the ICMP, ARP and NDP protocols that exist to support IP.
This kind of connectivity is suitable for VMs and workloads that only
communicate over IP.

Reachability between L3Networks
-------------------------------

All L3Networks automatically have reachability to each other.  In
other words, if one L3Network includes 10.65.0.3, and a second
L3Network includes 7.68.4.5, then 10.65.0.3 can ping 7.68.4.5, and
vice versa, without the need for those L3Networks to be explicitly
associated (such as via a Neutron router).  (All subject to security
policy, of course.)

(It might be useful in future to have an L3Network that does not have
automatic reachability to others, or perhaps to partition L3Networks
into groups, with reachability within each group, but not between
groups.  This is left for future work, as we have no use case for it
now.)

Alternatives
~~~~~~~~~~~~

When multiple L3Network objects are used, there are possible
alternatives to specifying (as just above) that they have automatic
mutual reachability.

- Reachability between L3Network objects could be required to be
  modeled by explicit API connections between those L3Network objects
  and a Neutron router, as is done currently with Neutron L2 networks.
  However that does not feel as natural as it does for L2 networks,
  because a L3Network will typically already use IP routing as part of
  its internal connectivity provision.

- It could be that the desired east-west reachability semantic is
  already what is implied by :code:`router:external True`, and so it
  would suffice for L3Network also to have the :code:`router:external`
  property, and for Calico to create its L3Network(s) with
  :code:`router:external True`.

L3Networks use the shared address space
---------------------------------------

All L3Networks use the shared address space.

(It might be useful in future to have L3Networks in private address
spaces, but this is left for future work.)

How Calico would use L3Network
------------------------------

The proposed L3Network object has the L3-only and uniform reachability
semantics that Calico needs for its mainline case (i.e. excluding its
future support for private address spaces), and allows the fixed IP
addressing patterns that Calico wants to use.

Depending on which turns out to be more natural and convenient, Calico
can either use a single L3Network object with multiple IPv4 and IPv6
subnets, or multiple L3Network objects each with one IPv4 and IPv6
subnet.  IP reachability is the same either way, but with a single
L3Network object the user also needs to specify which subnet each VM
should get its IP address from, when launching VMs.  :code:`neutron
port-create ...` supports this, so this is possible on the command
line using :code:`neutron port-create ...` followed by :code:`nova
boot --nic <port ID>`.  There does not appear to be any support in
Horizon, or for :code:`nova boot` without a pre-created port, but
these are implementation gaps that can easily be filled.

The uniform security policy semantic does not need anything further,
once we already have uniform L3Network port reachability.  Neutron
security groups can be used to define desired policy, and when applied
to L3Network ports will not be contingent on how those ports might be
partitioned into different L3Network objects.

Note that with this uniform reachability, it is still easy for a
particular tenant to get effective isolation, if desired, for its own
group of VMs.  The tenant just needs to create its own security group,
and use that security group when launching its own instances.

Calico's planned use of floating IPs (where IP mobility is needed) is
not supported by the current Neutron API - because current floating
IPs only work through Neutron routers - or addressed by this document,
so that will require further work.  Carl Baldwin's "Model changes..."
spec has begun exploring this.

Remaining questions
-------------------

How would an L3Network be relatable or connectable to other Neutron
objects, i.e. to Neutron (L2) networks, or routers, or subnets other
than those that are owned by L3Networks?  What would that mean?  The
use cases behind this spec do not require that, but the Neutron API
will need to pin down what is possible.

References
==========

Calico references:

- http://www.projectcalico.org/
- http://docs.openstack.org/developer/networking-calico
- https://git.openstack.org/cgit/openstack/networking-calico
- https://github.com/projectcalico/calico

Related bugs:

- https://bugs.launchpad.net/neutron/+bug/1472704 - My RFE bug
  requesting support for L3-only semantics for Calico.

- https://bugs.launchpad.net/neutron/+bug/1458890 - Large deployers'
  RFE bug.

Related work:

- https://review.openstack.org/#/c/198439/ - Previous incarnation of
  this proposal, now superseded by this spec.

- https://review.openstack.org/#/c/225384/ - Carl Baldwin's "Model
  changes to support routed network groups" spec, that primarily
  addresses the large deployers' RFE.

- https://wiki.openstack.org/wiki/Internship_ideas - Proposed
  Outreachy project to explore host-dependent pluggable IPAM.
