%global release_name icehouse

Name:		openstack-neutron
Version:	2014.1.1_calico0.5
Release:	1%{?dist}
Provides:	openstack-quantum = %{version}-%{release}
Obsoletes:	openstack-quantum < 2013.2-0.3.b3

Summary:	OpenStack Networking Service

Group:		Applications/System
License:	ASL 2.0
URL:		http://launchpad.net/neutron/

Source0:	http://launchpad.net/neutron/%{release_name}/%{version}/+download/neutron-%{version}.tar.gz
Source1:	neutron.logrotate
Source2:	neutron-sudoers

Source10:	neutron-server.init
Source20:	neutron-server.upstart
Source11:	neutron-linuxbridge-agent.init
Source21:	neutron-linuxbridge-agent.upstart
Source12:	neutron-openvswitch-agent.init
Source22:	neutron-openvswitch-agent.upstart
Source13:	neutron-ryu-agent.init
Source23:	neutron-ryu-agent.upstart
Source14:	neutron-nec-agent.init
Source24:	neutron-nec-agent.upstart
Source15:	neutron-dhcp-agent.init
Source25:	neutron-dhcp-agent.upstart
Source16:	neutron-l3-agent.init
Source26:	neutron-l3-agent.upstart
Source17:	neutron-metadata-agent.init
Source27:	neutron-metadata-agent.upstart
Source18:	neutron-ovs-cleanup.init
Source28:	neutron-ovs-cleanup.upstart
Source19:	neutron-lbaas-agent.init
Source29:	neutron-lbaas-agent.upstart
Source30:	neutron-mlnx-agent.init
Source40:	neutron-mlnx-agent.upstart
Source31:	neutron-vpn-agent.init
Source41:	neutron-vpn-agent.upstart
Source32:	neutron-metering-agent.init
Source42:	neutron-metering-agent.upstart

Source90:	neutron-dist.conf
#
# patches_base=2014.1.1+1
#
Patch0001: 0001-use-parallel-installed-versions-in-RHEL6.patch
Patch0002: 0002-Remove-dnsmasq-version-warning.patch
Patch0003: 0003-remove-runtime-dependency-on-pbr.patch
Patch0004: 0004-Sync-service-and-systemd-modules-from-oslo-incubator.patch
Patch0005: 0005-Removed-signing_dir-from-neutron.conf.patch
Patch0006: 0006-Remove-kernel-version-check-for-OVS-VXLAN.patch
Patch0007: 0007-Ensure-routing-key-is-specified-in-the-address-for-a.patch

BuildArch:	noarch

BuildRequires:	python2-devel
BuildRequires:	python-setuptools
# Build require these parallel versions
# as setup.py build imports neutron.openstack.common.setup
# which will then check for these
BuildRequires:	python-sqlalchemy0.7
BuildRequires:	python-webob1.2
BuildRequires:	python-paste-deploy1.5
BuildRequires:	python-routes1.12
BuildRequires:  python-jinja2-26
BuildRequires:	dos2unix
BuildRequires:	python-pbr
BuildRequires:	python-d2to1

Requires:	dnsmasq-utils
Requires:	python-neutron = %{version}-%{release}
Requires:	python-oslo-rootwrap
Requires:	openstack-utils

Requires(post):		chkconfig
Requires(postun):	initscripts
Requires(preun):	chkconfig
Requires(preun):	initscripts
Requires(pre):		shadow-utils

# dnsmasq is not a hard requirement, but is currently the only option
# when neutron-dhcp-agent is deployed.
Requires:	dnsmasq


%description
Neutron is a virtual network service for Openstack. Just like
OpenStack Nova provides an API to dynamically request and configure
virtual servers, Neutron provides an API to dynamically request and
configure virtual networks. These networks connect "interfaces" from
other OpenStack services (e.g., virtual NICs from Nova VMs). The
Neutron API supports extensions to provide advanced network
capabilities (e.g., QoS, ACLs, network monitoring, etc.)


%package -n python-neutron
Summary:	Neutron Python libraries
Group:		Applications/System

Provides:	python-quantum = %{version}-%{release}
Obsoletes:	python-quantum < 2013.2-0.3.b3

Requires:	MySQL-python
Requires:	python-alembic
Requires:	python-amqplib
Requires:	python-anyjson
Requires:	python-babel
Requires:	python-eventlet
Requires:	python-greenlet
Requires:	python-httplib2 >= 0.7.5
Requires:	python-iso8601
Requires:	python-jinja2-26
Requires:	python-keystoneclient >= 0.7.0
Requires:	python-kombu
Requires:	python-lxml
Requires:	python-oslo-rootwrap
Requires:	python-paste-deploy1.5
Requires:	python-routes1.12
Requires:	python-sqlalchemy0.7 >= 0.7.8
Requires:	python-webob1.2 >= 1.2.3
Requires:	python-netaddr
Requires:	python-oslo-config >= 1:1.2.0
Requires:	python-qpid
Requires:	python-neutronclient >= 2.3.4
Requires:	python-stevedore
Requires:	python-six >= 1.4.1
# requires.txt six >=1.5.2 actually
Requires:	python-novaclient >= 1:2.17.0
Requires:	sudo

%description -n python-neutron
Neutron provides an API to dynamically request and configure virtual
networks.

This package contains the neutron Python library.


%package bigswitch
Summary:	Neutron Big Switch plugin
Group:		Applications/System

Provides:	openstack-quantum-bigswitch = %{version}-%{release}
Obsoletes:	openstack-quantum-bigswitch < 2013.2-0.3.b3

Requires:	openstack-neutron = %{version}-%{release}


%description bigswitch
Neutron provides an API to dynamically request and configure virtual
networks.

This package contains the neutron plugin that implements virtual
networks using the FloodLight Openflow Controller or the Big Switch
Networks Controller.


%package brocade
Summary:	Neutron Brocade plugin
Group:		Applications/System

Provides:	openstack-quantum-brocade = %{version}-%{release}
Obsoletes:	openstack-quantum-brocade < 2013.2-0.3.b3

Requires:	openstack-neutron = %{version}-%{release}


%description brocade
Neutron provides an API to dynamically request and configure virtual
networks.

This package contains the neutron plugin that implements virtual
networks using Brocade VCS switches running NOS.


%package cisco
Summary:	Neutron Cisco plugin
Group:		Applications/System

Provides:	openstack-quantum-cisco = %{version}-%{release}
Obsoletes:	openstack-quantum-cisco < 2013.2-0.3.b3

Requires:	openstack-neutron = %{version}-%{release}
Requires:	python-configobj


%description cisco
Neutron provides an API to dynamically request and configure virtual
networks.

This package contains the neutron plugin that implements virtual
networks using Cisco UCS and Nexus.


%package hyperv
Summary:	Neutron Hyper-V plugin
Group:		Applications/System

Provides:	openstack-quantum-hyperv = %{version}-%{release}
Obsoletes:	openstack-quantum-hyperv < 2013.2-0.3.b3

Requires:	openstack-neutron = %{version}-%{release}


%description hyperv
Neutron provides an API to dynamically request and configure virtual
networks.

This package contains the neutron plugin that implements virtual
networks using Microsoft Hyper-V.


%package ibm
Summary:	Neutron IBM plugin
Group:		Applications/System

Requires:	openstack-neutron = %{version}-%{release}


%description ibm
Neutron provides an API to dynamically request and configure virtual
networks.

This package contains the neutron plugin that implements virtual
networks from IBM.


%package linuxbridge
Summary:	Neutron linuxbridge plugin
Group:		Applications/System

Provides:	openstack-quantum-linuxbridge = %{version}-%{release}
Obsoletes:	openstack-quantum-linuxbridge < 2013.2-0.3.b3

Requires:	bridge-utils
Requires:	openstack-neutron = %{version}-%{release}


%description linuxbridge
Neutron provides an API to dynamically request and configure virtual
networks.

This package contains the neutron plugin that implements virtual
networks as VLANs using Linux bridging.


%package midonet
Summary:	Neutron MidoNet plugin
Group:		Applications/System

Provides:	openstack-quantum-midonet = %{version}-%{release}
Obsoletes:	openstack-quantum-midonet < 2013.2-0.3.b3

Requires:	openstack-neutron = %{version}-%{release}


%description midonet
Neutron provides an API to dynamically request and configure virtual
networks.

This package contains the neutron plugin that implements virtual
networks using MidoNet from Midokura.


%package ml2
Summary:	Neutron ML2 plugin
Group:		Applications/System

Provides:	openstack-quantum-ml2 = %{version}-%{release}
Obsoletes:	openstack-quantum-ml2 < 2013.2-0.3.b3

Requires:	openstack-neutron = %{version}-%{release}


%description ml2
Neutron provides an API to dynamically request and configure virtual
networks.

This package contains a neutron plugin that allows the use of drivers
to support separately extensible sets of network types and the mechanisms
for accessing those types.


%package mellanox
Summary:	Neutron Mellanox plugin
Group:		Applications/System

Provides:	openstack-quantum-mellanox = %{version}-%{release}
Obsoletes:	openstack-quantum-mellanox < 2013.2-0.3.b3

Requires:	openstack-neutron = %{version}-%{release}


%description mellanox
This plugin implements Neutron v2 APIs with support for Mellanox embedded
switch functionality as part of the VPI (Ethernet/InfiniBand) HCA.


%package nuage
Summary:    Neutron Nuage plugin
Group:      Applications/System

Requires:   openstack-neutron = %{version}-%{release}


%description nuage
This plugin implements Neutron v2 APIs with support for Nuage Networks
Virtual Service Platform (VSP).


%package ofagent
Summary:	Neutron ofagent plugin from ryu project
Group:		Applications/system

Requires:	openstack-neutron = %{version}-%{release}

%description ofagent
This plugin implements Neutron v2 APIs with support for the ryu ofagent
plugin.


%package oneconvergence-nvsd
Summary:       Neutron One Convergence NVSD plugin
Group:         Applications/System

Requires:      openstack-neutron = %{version}-%{release}


%description oneconvergence-nvsd
Neutron provides an API to dynamnically request and configure virtual
networks.

This package contains the neutron plugin that implements virtual
networks using One Convergence NVSD


%package openvswitch
Summary:	Neutron openvswitch plugin
Group:		Applications/System

Provides:	openstack-quantum-openvswitch = %{version}-%{release}
Obsoletes:	openstack-quantum-openvswitch < 2013.2-0.3.b3

Requires:	openstack-neutron = %{version}-%{release}
Requires:	openvswitch


%description openvswitch
Neutron provides an API to dynamically request and configure virtual
networks.

This package contains the neutron plugin that implements virtual
networks using Open vSwitch.


%package plumgrid
Summary:	Neutron PLUMgrid plugin
Group:		Applications/System

Provides:	openstack-quantum-plumgrid = %{version}-%{release}
Obsoletes:	openstack-quantum-plumgrid < 2013.2-0.3.b3

Requires:	openstack-neutron = %{version}-%{release}


%description plumgrid
Neutron provides an API to dynamically request and configure virtual
networks.

This package contains the neutron plugin that implements virtual
networks using the PLUMgrid platform.


%package ryu
Summary:	Neutron Ryu plugin
Group:		Applications/System

Provides:	openstack-quantum-ryu = %{version}-%{release}
Obsoletes:	openstack-quantum-ryu < 2013.2-0.3.b3

Requires:	openstack-neutron = %{version}-%{release}


%description ryu
Neutron provides an API to dynamically request and configure virtual
networks.

This package contains the neutron plugin that implements virtual
networks using the Ryu Network Operating System.


%package nec
Summary:	Neutron NEC plugin
Group:		Applications/System

Provides:	openstack-quantum-nec = %{version}-%{release}
Obsoletes:	openstack-quantum-nec < 2013.2-0.3.b3

Requires:	openstack-neutron = %{version}-%{release}


%description nec
Neutron provides an API to dynamically request and configure virtual
networks.

This package contains the neutron plugin that implements virtual
networks using the NEC OpenFlow controller.


%package metaplugin
Summary:	Neutron meta plugin
Group:		Applications/System

Provides:	openstack-quantum-metaplugin = %{version}-%{release}
Obsoletes:	openstack-quantum-metaplugin < 2013.2-0.3.b3

Requires:	openstack-neutron = %{version}-%{release}


%description metaplugin
Neutron provides an API to dynamically request and configure virtual
networks.

This package contains the neutron plugin that implements virtual
networks using multiple other neutron plugins.


%package vmware
Summary:       Neutron VMWare NSX support
Group:         Applications/System

Requires:      openstack-neutron = %{version}-%{release}
Provides:      openstack-neutron-nicira = %{version}-%{release}
Obsoletes:     openstack-neutron-nicira < 2014.1-4

%description vmware
This package adds VMWare NSX support for neutron


%package metering-agent
Summary:	Neutron bandwidth metering agent
Group:		Applications/System

Requires:	openstack-neutron = %{version}-%{release}

%description metering-agent
Neutron provides an API to measure bandwidth utilization

This package contains the neutron agent responsible for generating bandwidth
utilization notifications.


%package vpn-agent
Summary:	Neutron VPNaaS agent
Group:		Applications/System

Requires:	openstack-neutron = %{version}-%{release}

%description vpn-agent
Neutron provides an API to implement VPN as a service

This package contains the neutron agent responsible for implenting VPNaaS with
IPSec.


%prep
%setup -q -n neutron-%{version}

%patch0001 -p1
%patch0002 -p1
%patch0003 -p1
%patch0004 -p1
%patch0005 -p1
%patch0006 -p1
%patch0007 -p1

find neutron -name \*.py -exec sed -i '/\/usr\/bin\/env python/{d;q}' {} +

# Ensure SOURCES.txt ends in a newline and if any patches have added files, append them to SOURCES.txt
[ -n "$(tail -c 1 < neutron.egg-info/SOURCES.txt)" ] && echo >> neutron.egg-info/SOURCES.txt
if ls %{_sourcedir}/*.patch >/dev/null 2>&1; then
awk '/^new file/ {split(a,files," ");print substr(files[3],3)} {a = $0}' %{_sourcedir}/*.patch >> neutron.egg-info/SOURCES.txt
fi

sed -i 's/RPMVERSION/%{version}/; s/RPMRELEASE/%{release}/' neutron/version.py

chmod 644 neutron/plugins/cisco/README

# Let's handle dependencies ourseleves
rm -f requirements.txt

%build
%{__python} setup.py build

# Loop through values in neutron-dist.conf and make sure that the values
# are substituted into the neutron.conf as comments. Some of these values
# will have been uncommented as a way of upstream setting defaults outside
# of the code. For service_provider and notification-driver, there are
# commented examples above uncommented settings, so this specifically
# skips those comments and instead comments out the actual settings and
# substitutes the correct default values.
while read name eq value; do
  test "$name" && test "$value" || continue
  if [ "$name" = "service_provider" -o "$name" = "notification_driver" ]; then
    sed -ri "0,/^$name *=/{s!^$name *=.*!# $name = $value!}" etc/neutron.conf
  else
    sed -ri "0,/^(#)? *$name *=/{s!^(#)? *$name *=.*!# $name = $value!}" etc/neutron.conf
  fi
done < %{SOURCE90}

%install
%{__python} setup.py install -O1 --skip-build --root %{buildroot}

# Remove unused files
rm -rf %{buildroot}%{python_sitelib}/bin
rm -rf %{buildroot}%{python_sitelib}/doc
rm -rf %{buildroot}%{python_sitelib}/tools
rm -rf %{buildroot}%{python_sitelib}/neutron/tests
rm -rf %{buildroot}%{python_sitelib}/neutron/plugins/*/tests
rm -f %{buildroot}%{python_sitelib}/neutron/plugins/*/run_tests.*
rm %{buildroot}/usr/etc/init.d/neutron-server

# Move rootwrap files to proper location
install -d -m 755 %{buildroot}%{_datarootdir}/neutron/rootwrap
mv %{buildroot}/usr/etc/neutron/rootwrap.d/*.filters %{buildroot}%{_datarootdir}/neutron/rootwrap

# Move config files to proper location
install -d -m 755 %{buildroot}%{_sysconfdir}/neutron
mv %{buildroot}/usr/etc/neutron/* %{buildroot}%{_sysconfdir}/neutron
mv %{buildroot}%{_sysconfdir}/neutron/api-paste.ini %{buildroot}%{_datadir}/neutron/api-paste.ini
chmod 640  %{buildroot}%{_sysconfdir}/neutron/plugins/*/*.ini

# TODO: remove this once the plugin is separately packaged
rm %{buildroot}%{_sysconfdir}/neutron/plugins/embrane/heleos_conf.ini

# Install logrotate
install -p -D -m 644 %{SOURCE1} %{buildroot}%{_sysconfdir}/logrotate.d/openstack-neutron

# Install sudoers
install -p -D -m 440 %{SOURCE2} %{buildroot}%{_sysconfdir}/sudoers.d/neutron

# Install sysv init scripts
install -p -D -m 755 %{SOURCE10} %{buildroot}%{_initrddir}/neutron-server
install -p -D -m 755 %{SOURCE11} %{buildroot}%{_initrddir}/neutron-linuxbridge-agent
install -p -D -m 755 %{SOURCE12} %{buildroot}%{_initrddir}/neutron-openvswitch-agent
install -p -D -m 755 %{SOURCE13} %{buildroot}%{_initrddir}/neutron-ryu-agent
install -p -D -m 755 %{SOURCE14} %{buildroot}%{_initrddir}/neutron-nec-agent
install -p -D -m 755 %{SOURCE15} %{buildroot}%{_initrddir}/neutron-dhcp-agent
install -p -D -m 755 %{SOURCE16} %{buildroot}%{_initrddir}/neutron-l3-agent
install -p -D -m 755 %{SOURCE17} %{buildroot}%{_initrddir}/neutron-metadata-agent
install -p -D -m 755 %{SOURCE18} %{buildroot}%{_initrddir}/neutron-ovs-cleanup
install -p -D -m 755 %{SOURCE19} %{buildroot}%{_initrddir}/neutron-lbaas-agent
install -p -D -m 755 %{SOURCE30} %{buildroot}%{_initrddir}/neutron-mlnx-agent
install -p -D -m 755 %{SOURCE31} %{buildroot}%{_initrddir}/neutron-vpn-agent
install -p -D -m 755 %{SOURCE32} %{buildroot}%{_initrddir}/neutron-metering-agent

# Setup directories
install -d -m 755 %{buildroot}%{_datadir}/neutron
install -d -m 755 %{buildroot}%{_sharedstatedir}/neutron
install -d -m 755 %{buildroot}%{_localstatedir}/log/neutron
install -d -m 755 %{buildroot}%{_localstatedir}/run/neutron

# Install upstart jobs examples
install -p -m 644 %{SOURCE20} %{buildroot}%{_datadir}/neutron/
install -p -m 644 %{SOURCE21} %{buildroot}%{_datadir}/neutron/
install -p -m 644 %{SOURCE22} %{buildroot}%{_datadir}/neutron/
install -p -m 644 %{SOURCE23} %{buildroot}%{_datadir}/neutron/
install -p -m 644 %{SOURCE24} %{buildroot}%{_datadir}/neutron/
install -p -m 644 %{SOURCE25} %{buildroot}%{_datadir}/neutron/
install -p -m 644 %{SOURCE26} %{buildroot}%{_datadir}/neutron/
install -p -m 644 %{SOURCE27} %{buildroot}%{_datadir}/neutron/
install -p -m 644 %{SOURCE28} %{buildroot}%{_datadir}/neutron/
install -p -m 644 %{SOURCE29} %{buildroot}%{_datadir}/neutron/
install -p -m 644 %{SOURCE40} %{buildroot}%{_datadir}/neutron/
install -p -m 644 %{SOURCE41} %{buildroot}%{_datadir}/neutron/
install -p -m 644 %{SOURCE42} %{buildroot}%{_datadir}/neutron/

# Install dist conf
install -p -D -m 640 %{SOURCE90} %{buildroot}%{_datadir}/neutron/neutron-dist.conf

# Install version info file
cat > %{buildroot}%{_sysconfdir}/neutron/release <<EOF
[Neutron]
vendor = Fedora Project
product = OpenStack Neutron
package = %{release}
EOF

%pre
getent group neutron >/dev/null || groupadd -r neutron
getent passwd neutron >/dev/null || \
    useradd -r -g neutron -d %{_sharedstatedir}/neutron -s /sbin/nologin \
    -c "OpenStack Neutron Daemons" neutron
exit 0


%post
if [ $1 -eq 1 ] ; then
    # Initial installation
    /sbin/chkconfig --add neutron-server
    for agent in dhcp l3 metadata lbaas; do
      /sbin/chkconfig --add neutron-$agent-agent
    done
fi

%preun
if [ $1 -eq 0 ] ; then
    # Package removal, not upgrade
    /sbin/service neutron-server stop >/dev/null 2>&1
    /sbin/chkconfig --del neutron-server
    for agent in dhcp l3 metadata lbaas; do
      /sbin/service neutron-$agent-agent stop >/dev/null 2>&1
      /sbin/chkconfig --del neutron-$agent-agent
    done
fi

%postun
if [ $1 -ge 1 ] ; then
    # Package upgrade, not uninstall
    /sbin/service neutron-server condrestart >/dev/null 2>&1 || :
    for agent in dhcp l3 metadata lbaas; do
      /sbin/service neutron-$agent-agent condrestart >/dev/null 2>&1 || :
    done
fi

%pretrans
if rpm --quiet -q openstack-quantum; then
    mkdir -p  %{_localstatedir}/lib/rpm-state/

    # Create a script for restoring init script enabling that we can also
    # use as a flag to detect quantum -> grizzly upgrades in %posttrans
    chkconfig --type sysv --list|grep ^quantum| \
      sed -re 's/[0-6]:off//g
               s/([0-6]):on\s*/\1/g
               s/quantum/neutron/g
               s/^([a-z0-9-]+)\s+$/chkconfig \1 off/
               s/^([a-z0-9-]+)\s+([0-6]+)/chkconfig --levels \2 \1 on/' > %{_localstatedir}/lib/rpm-state/UPGRADE_FROM_QUANTUM
fi

%posttrans
# Handle migration from quantum -> neutron
if [ -e %{_localstatedir}/lib/rpm-state/UPGRADE_FROM_QUANTUM ];then
    # Migrate existing config files
    for i in `find /etc/quantum -name *.rpmsave`;do
        new=${i//quantum/neutron}
        new=${new/%.rpmsave/}
        sed -e '/^sql_connection/ b
                /^admin_user/ b
                s/quantum/neutron/g
                s/Quantum/Neutron/g' $i > $new
    done

    # Re-create plugin.ini if it existed.
    if [ -h %{_sysconfdir}/quantum/plugin.ini ];then
        plugin_ini=$(readlink %{_sysconfdir}/quantum/plugin.ini)
        ln -s ${plugin_ini//quantum/neutron} %{_sysconfdir}/neutron/plugin.ini
    fi

    # Stamp the existing db as grizzly to avoid neutron-server breaking db migration
    neutron-db-manage --config-file %{_sysconfdir}/neutron/neutron.conf --config-file %{_sysconfdir}/neutron/plugin.ini stamp grizzly || :

    # Restore the enablement of the various neutron services
    source %{_localstatedir}/lib/rpm-state/UPGRADE_FROM_QUANTUM

    rm -f %{_localstatedir}/lib/rpm-state/UPGRADE_FROM_QUANTUM
fi


%post linuxbridge
if [ $1 -eq 1 ] ; then
    # Initial installation
    /sbin/chkconfig --add neutron-linuxbridge-agent
fi

%preun linuxbridge
if [ $1 -eq 0 ] ; then
    # Package removal, not upgrade
    /sbin/service neutron-linuxbridge-agent stop >/dev/null 2>&1
    /sbin/chkconfig --del neutron-linuxbridge-agent
fi

%postun linuxbridge
if [ $1 -ge 1 ] ; then
    # Package upgrade, not uninstall
    /sbin/service neutron-linuxbridge-agent condrestart >/dev/null 2>&1 || :
fi


%post openvswitch
if [ $1 -eq 1 ] ; then
    # Initial installation
    /sbin/chkconfig --add neutron-openvswitch-agent
fi

%preun openvswitch
if [ $1 -eq 0 ] ; then
    # Package removal, not upgrade
    /sbin/service neutron-openvswitch-agent stop >/dev/null 2>&1
    /sbin/chkconfig --del neutron-openvswitch-agent
fi

%postun openvswitch
if [ $1 -ge 1 ] ; then
    # Package upgrade, not uninstall
    /sbin/service neutron-openvswitch-agent condrestart >/dev/null 2>&1 || :
fi


%post ryu
if [ $1 -eq 1 ] ; then
    # Initial installation
    /sbin/chkconfig --add neutron-ryu-agent
fi

%preun ryu
if [ $1 -eq 0 ] ; then
    # Package removal, not upgrade
    /sbin/service neutron-ryu-agent stop >/dev/null 2>&1
    /sbin/chkconfig --del neutron-ryu-agent
fi

%postun ryu
if [ $1 -ge 1 ] ; then
    # Package upgrade, not uninstall
    /sbin/service neutron-ryu-agent condrestart >/dev/null 2>&1 || :
fi


%post nec
if [ $1 -eq 1 ] ; then
    # Initial installation
    /sbin/chkconfig --add neutron-nec-agent
fi

%preun nec
if [ $1 -eq 0 ] ; then
    # Package removal, not upgrade
    /sbin/service neutron-nec-agent stop >/dev/null 2>&1
    /sbin/chkconfig --del neutron-nec-agent
fi


%postun nec
/bin/systemctl daemon-reload >/dev/null 2>&1 || :
if [ $1 -ge 1 ] ; then
    # Package upgrade, not uninstall
    /sbin/service neutron-nec-agent condrestart >/dev/null 2>&1 || :
fi


%post mellanox
if [ $1 -eq 1 ] ; then
    # Initial installation
    /sbin/chkconfig --add neutron-mlnx-agent
fi

%preun mellanox
if [ $1 -eq 0 ] ; then
    # Package removal, not upgrade
    /sbin/service neutron-mlnx-agent stop >/dev/null 2>&1
    /sbin/chkconfig --del neutron-mlnx-agent
fi

%postun mellanox
if [ $1 -ge 1 ] ; then
    # Package upgrade, not uninstall
    /sbin/service neutron-mlnx-agent condrestart >/dev/null 2>&1 || :
fi


%post vpn-agent
if [ $1 -eq 1 ] ; then
    # Initial installation
    /sbin/chkconfig --add neutron-vpn-agent
fi

%preun vpn-agent
if [ $1 -eq 0 ] ; then
    # Package removal, not upgrade
    /sbin/service neutron-vpn-agent stop >/dev/null 2>&1
    /sbin/chkconfig --del neutron-vpn-agent
fi

%postun vpn-agent
if [ $1 -ge 1 ] ; then
    # Package upgrade, not uninstall
    /sbin/service neutron-vpn-agent condrestart >/dev/null 2>&1 || :
fi


%post metering-agent
if [ $1 -eq 1 ] ; then
    # Initial installation
    /sbin/chkconfig --add neutron-metering-agent
fi

%preun metering-agent
if [ $1 -eq 0 ] ; then
    # Package removal, not upgrade
    /sbin/service neutron-metering-agent stop >/dev/null 2>&1
    /sbin/chkconfig --del neutron-metering-agent
fi

%postun metering-agent
if [ $1 -ge 1 ] ; then
    # Package upgrade, not uninstall
    /sbin/service neutron-metering-agent condrestart >/dev/null 2>&1 || :
fi

%files
%doc LICENSE
%doc README.rst
%{_bindir}/quantum-db-manage
%{_bindir}/quantum-debug
%{_bindir}/quantum-dhcp-agent
%{_bindir}/quantum-l3-agent
%{_bindir}/quantum-lbaas-agent
%{_bindir}/quantum-metadata-agent
%{_bindir}/quantum-netns-cleanup
%{_bindir}/quantum-ns-metadata-proxy
%{_bindir}/quantum-rootwrap
%{_bindir}/quantum-rootwrap-xen-dom0
%{_bindir}/quantum-server
%{_bindir}/quantum-usage-audit

%{_bindir}/neutron-db-manage
%{_bindir}/neutron-debug
%{_bindir}/neutron-dhcp-agent
%{_bindir}/neutron-l3-agent
%{_bindir}/neutron-lbaas-agent
%{_bindir}/neutron-metadata-agent
%{_bindir}/neutron-netns-cleanup
%{_bindir}/neutron-ns-metadata-proxy
%{_bindir}/neutron-rootwrap
%{_bindir}/neutron-rootwrap-xen-dom0
%{_bindir}/neutron-server
%{_bindir}/neutron-usage-audit

%{_initrddir}/neutron-server
%{_initrddir}/neutron-dhcp-agent
%{_initrddir}/neutron-l3-agent
%{_initrddir}/neutron-metadata-agent
%{_initrddir}/neutron-ovs-cleanup
%{_initrddir}/neutron-lbaas-agent
%dir %{_datadir}/neutron
%{_datadir}/neutron/neutron-server.upstart
%{_datadir}/neutron/neutron-dhcp-agent.upstart
%{_datadir}/neutron/neutron-metadata-agent.upstart
%{_datadir}/neutron/neutron-l3-agent.upstart
%{_datadir}/neutron/neutron-lbaas-agent.upstart
%dir %{_sysconfdir}/neutron
%{_sysconfdir}/neutron/release
%attr(-, root, neutron) %{_datadir}/neutron/neutron-dist.conf
%attr(-, root, neutron) %{_datadir}/neutron/api-paste.ini
%config(noreplace) %attr(0640, root, neutron) %{_sysconfdir}/neutron/dhcp_agent.ini
%config(noreplace) %attr(0640, root, neutron) %{_sysconfdir}/neutron/fwaas_driver.ini
%config(noreplace) %attr(0640, root, neutron) %{_sysconfdir}/neutron/l3_agent.ini
%config(noreplace) %attr(0640, root, neutron) %{_sysconfdir}/neutron/metadata_agent.ini
%config(noreplace) %attr(0640, root, neutron) %{_sysconfdir}/neutron/lbaas_agent.ini
%config(noreplace) %attr(0640, root, neutron) %{_sysconfdir}/neutron/policy.json
%config(noreplace) %attr(0640, root, neutron) %{_sysconfdir}/neutron/neutron.conf
%config(noreplace) %{_sysconfdir}/neutron/rootwrap.conf
%dir %{_sysconfdir}/neutron/plugins
%config(noreplace) %{_sysconfdir}/logrotate.d/*
%config(noreplace) %{_sysconfdir}/sudoers.d/neutron
%dir %attr(0755, neutron, neutron) %{_sharedstatedir}/neutron
%dir %attr(0755, neutron, neutron) %{_localstatedir}/log/neutron
%dir %attr(0755, neutron, neutron) %{_localstatedir}/run/neutron
%dir %{_datarootdir}/neutron/rootwrap
%{_datarootdir}/neutron/rootwrap/debug.filters
%{_datarootdir}/neutron/rootwrap/dhcp.filters
%{_datarootdir}/neutron/rootwrap/iptables-firewall.filters
%{_datarootdir}/neutron/rootwrap/l3.filters
%{_datarootdir}/neutron/rootwrap/lbaas-haproxy.filters


%files -n python-neutron
%doc LICENSE
%doc README.rst
%{python_sitelib}/neutron
%{python_sitelib}/quantum
%exclude %{python_sitelib}/neutron/plugins/bigswitch
%exclude %{python_sitelib}/neutron/plugins/brocade
%exclude %{python_sitelib}/neutron/plugins/cisco
%exclude %{python_sitelib}/neutron/plugins/hyperv
%exclude %{python_sitelib}/neutron/plugins/ibm
%exclude %{python_sitelib}/neutron/plugins/linuxbridge
%exclude %{python_sitelib}/neutron/plugins/metaplugin
%exclude %{python_sitelib}/neutron/plugins/midonet
%exclude %{python_sitelib}/neutron/plugins/ml2
%exclude %{python_sitelib}/neutron/plugins/mlnx
%exclude %{python_sitelib}/neutron/plugins/nuage
%exclude %{python_sitelib}/neutron/plugins/nec
%exclude %{python_sitelib}/neutron/plugins/nicira
%exclude %{python_sitelib}/neutron/plugins/ofagent
%exclude %{python_sitelib}/neutron/plugins/oneconvergence
%exclude %{python_sitelib}/neutron/plugins/openvswitch
%exclude %{python_sitelib}/neutron/plugins/plumgrid
%exclude %{python_sitelib}/neutron/plugins/ryu
%exclude %{python_sitelib}/neutron/plugins/vmware
%{python_sitelib}/neutron-%%{version}*.egg-info


%files bigswitch
%doc LICENSE
%doc neutron/plugins/bigswitch/README
%{_bindir}/neutron-restproxy-agent
%{python_sitelib}/neutron/plugins/bigswitch
%dir %{_sysconfdir}/neutron/plugins/bigswitch
%config(noreplace) %attr(0640, root, neutron) %{_sysconfdir}/neutron/plugins/bigswitch/*.ini
%doc %{_sysconfdir}/neutron/plugins/bigswitch/README


%files brocade
%doc LICENSE
%doc neutron/plugins/brocade/README.md
%{python_sitelib}/neutron/plugins/brocade
%dir %{_sysconfdir}/neutron/plugins/brocade
%config(noreplace) %attr(0640, root, neutron) %{_sysconfdir}/neutron/plugins/brocade/*.ini


%files cisco
%doc LICENSE
%doc neutron/plugins/cisco/README
%{python_sitelib}/neutron/plugins/cisco
%dir %{_sysconfdir}/neutron/plugins/cisco
%config(noreplace) %attr(0640, root, neutron) %{_sysconfdir}/neutron/plugins/cisco/*.ini


%files hyperv
%doc LICENSE
#%%doc neutron/plugins/hyperv/README
%{_bindir}/neutron-hyperv-agent
%{_bindir}/quantum-hyperv-agent
%{python_sitelib}/neutron/plugins/hyperv
%dir %{_sysconfdir}/neutron/plugins/hyperv
%exclude %{python_sitelib}/neutron/plugins/hyperv/agent
%config(noreplace) %attr(0640, root, neutron) %{_sysconfdir}/neutron/plugins/hyperv/*.ini


%files ibm
%doc LICENSE
%{_bindir}/neutron-ibm-agent
%{_bindir}/quantum-ibm-agent
%doc neutron/plugins/ibm/README
%{python_sitelib}/neutron/plugins/ibm
%dir %{_sysconfdir}/neutron/plugins/ibm
%config(noreplace) %attr(0640, root, neutron) %{_sysconfdir}/neutron/plugins/ibm/*.ini


%files linuxbridge
%doc LICENSE
%doc neutron/plugins/linuxbridge/README
%{_bindir}/neutron-linuxbridge-agent
%{_bindir}/quantum-linuxbridge-agent
%{_initrddir}/neutron-linuxbridge-agent
%{_datadir}/neutron/neutron-linuxbridge-agent.upstart
%{python_sitelib}/neutron/plugins/linuxbridge
%{_datarootdir}/neutron/rootwrap/linuxbridge-plugin.filters
%dir %{_sysconfdir}/neutron/plugins/linuxbridge
%config(noreplace) %attr(0640, root, neutron) %{_sysconfdir}/neutron/plugins/linuxbridge/*.ini


%files midonet
%doc LICENSE
#%%doc neutron/plugins/midonet/README
%{python_sitelib}/neutron/plugins/midonet
%dir %{_sysconfdir}/neutron/plugins/midonet
%config(noreplace) %attr(0640, root, neutron) %{_sysconfdir}/neutron/plugins/midonet/*.ini


%files ml2
%doc neutron/plugins/ml2/README
%{python_sitelib}/neutron/plugins/ml2
%dir %{_sysconfdir}/neutron/plugins/ml2
%config(noreplace) %attr(0640, root, neutron) %{_sysconfdir}/neutron/plugins/ml2/*.ini


%files mellanox
%doc neutron/plugins/mlnx/README
%{_bindir}/neutron-mlnx-agent
%{_bindir}/quantum-mlnx-agent
%{python_sitelib}/neutron/plugins/mlnx
%{_initrddir}/neutron-mlnx-agent
%{_datadir}/neutron/neutron-mlnx-agent.upstart
%dir %{_sysconfdir}/neutron/plugins/mlnx
%config(noreplace) %attr(0640, root, neutron) %{_sysconfdir}/neutron/plugins/mlnx/*.ini

%files nuage
%doc LICENSE
%{python_sitelib}/neutron/plugins/nuage
%dir %{_sysconfdir}/neutron/plugins/nuage
%config(noreplace) %attr(0640, root, neutron) %{_sysconfdir}/neutron/plugins/nuage/*.ini

%files ofagent
%doc neutron/plugins/ofagent/README
%{_bindir}/neutron-ofagent-agent
%{python_sitelib}/neutron/plugins/ofagent


%files oneconvergence-nvsd
%doc LICENSE
%doc neutron/plugins/oneconvergence/README
%dir %{_sysconfdir}/neutron/plugins/oneconvergence
%config(noreplace) %attr(0640, root, neutron) %{_sysconfdir}/neutron/plugins/oneconvergence/nvsdplugin.ini
%{_bindir}/neutron-nvsd-agent
%{_bindir}/quantum-nvsd-agent
%{python_sitelib}/neutron/plugins/oneconvergence


%files openvswitch
%doc LICENSE
%doc neutron/plugins/openvswitch/README
%{_bindir}/neutron-openvswitch-agent
%{_bindir}/quantum-openvswitch-agent
%{_bindir}/neutron-ovs-cleanup
%{_bindir}/quantum-ovs-cleanup
%{_initrddir}/neutron-openvswitch-agent
%{_datadir}/neutron/neutron-openvswitch-agent.upstart
%{_initrddir}/neutron-ovs-cleanup
%{_datadir}/neutron/neutron-ovs-cleanup.upstart
%{python_sitelib}/neutron/plugins/openvswitch
%{_datarootdir}/neutron/rootwrap/openvswitch-plugin.filters
%dir %{_sysconfdir}/neutron/plugins/openvswitch
%config(noreplace) %attr(0640, root, neutron) %{_sysconfdir}/neutron/plugins/openvswitch/*.ini


%files plumgrid
%doc LICENSE
%doc neutron/plugins/plumgrid/README
%{python_sitelib}/neutron/plugins/plumgrid
%dir %{_sysconfdir}/neutron/plugins/plumgrid
%config(noreplace) %attr(0640, root, neutron) %{_sysconfdir}/neutron/plugins/plumgrid/*.ini


%files ryu
%doc LICENSE
%doc neutron/plugins/ryu/README
%{_bindir}/neutron-ryu-agent
%{_bindir}/quantum-ryu-agent
%{_initrddir}/neutron-ryu-agent
%{_datadir}/neutron/neutron-ryu-agent.upstart
%{python_sitelib}/neutron/plugins/ryu
%{_datarootdir}/neutron/rootwrap/ryu-plugin.filters
%dir %{_sysconfdir}/neutron/plugins/ryu
%config(noreplace) %attr(0640, root, neutron) %{_sysconfdir}/neutron/plugins/ryu/*.ini


%files nec
%doc LICENSE
%doc neutron/plugins/nec/README
%{_bindir}/neutron-nec-agent
%{_bindir}/quantum-nec-agent
%{_initrddir}/neutron-nec-agent
%{_datadir}/neutron/neutron-nec-agent.upstart
%{python_sitelib}/neutron/plugins/nec
%{_datarootdir}/neutron/rootwrap/nec-plugin.filters
%dir %{_sysconfdir}/neutron/plugins/nec
%config(noreplace) %attr(0640, root, neutron) %{_sysconfdir}/neutron/plugins/nec/*.ini


%files metaplugin
%doc LICENSE
%doc neutron/plugins/metaplugin/README
%{python_sitelib}/neutron/plugins/metaplugin
%dir %{_sysconfdir}/neutron/plugins/metaplugin
%config(noreplace) %attr(0640, root, neutron) %{_sysconfdir}/neutron/plugins/metaplugin/*.ini


%files metering-agent
%doc LICENSE
%config(noreplace) %attr(0640, root, neutron) %{_sysconfdir}/neutron/metering_agent.ini
%{_initrddir}/neutron-metering-agent
%{_datadir}/neutron/neutron-metering-agent.upstart
%{_bindir}/neutron-metering-agent


%files vmware
%doc LICENSE
%{_bindir}/neutron-check-nvp-config
%{_bindir}/quantum-check-nvp-config
%{_bindir}/neutron-check-nsx-config
%{_bindir}/neutron-nsx-manage
%{python_sitelib}/neutron/plugins/vmware
%dir %{_sysconfdir}/neutron/plugins/vmware
%dir %{_sysconfdir}/neutron/plugins/nicira
%config(noreplace) %attr(0640, root, neutron) %{_sysconfdir}/neutron/plugins/vmware/*.ini
%config(noreplace) %attr(0640, root, neutron) %{_sysconfdir}/neutron/plugins/nicira/*.ini


%files vpn-agent
%doc LICENSE
%config(noreplace) %attr(0640, root, neutron) %{_sysconfdir}/neutron/vpn_agent.ini
%{_initrddir}/neutron-vpn-agent
%{_datadir}/neutron/neutron-vpn-agent.upstart
%{_bindir}/neutron-vpn-agent
%{_datarootdir}/neutron/rootwrap/vpnaas.filters


%changelog
* Mon Oct 27 2014 Neil Jerram <nj@metaswitch.com> 2014.1.1_calico0.5-1
- Add Calico mechanism driver

* Tue Sep 16 2014 Neil Jerram <nj@metaswitch.com> 2014.1.1_calico0.4-1
- DHCP agent enhancements for Calico/IPv6 networking

* Mon Jul 21 2014 Neil Jerram <nj@metaswitch.com> 2014.1.1_calico0.3-1
- Support providing metadata in a flat routed network

* Tue Jul 08 2014 Neil Jerram <nj@metaswitch.com> 2014.1.1_calico0.2-1
- DHCP agent: correctly set the subnet mask on the interfaces used by DHCP

* Tue Jul 08 2014 Neil Jerram <nj@metaswitch.com> 2014.1.1_calico0.1-1
- Add VIF_TYPE constant for routed virtual interfaces.
- DHCP agent: support routed VM interfaces as well as bridged
- IPTables: support routed virtual interfaces as well as bridged
- ML2 plugin get_device_details: also return fixed IPs
- DHCP agent: ignore 'use_namespaces' config when serving routed VM interfaces

* Fri Jun 13 2014 Ihar Hrachyshka <ihrachys@redhat.com> 2014.1.1-1
- Update to upstream 2014.1.1
- Added previously missing ml2_conf_mlnx.ini, bz#1100136

* Wed Jun 11 2014 Ihar Hrachyshka <ihrachys@redhat.com> 2014.1-21
- Ensure routing key is specified in the address for a direct producer, bz#1108025

* Thu May 29 2014 Miguel Ángel Ajo <majopela@redhat.com> 2014.1-20
- Add nuage plugin packaging as openstack-neutron-nuage

* Wed May 28 2014 Miguel Angel Ajo <majopela@redhat.com> 2014.1-19
- Remove kernel version check for OVS VXLAN, not revelant for RDO
  bz#1081011

* Mon May 19 2014 Ihar Hrachyshka <ihrachys@redhat.com> 2014.1-18
- netaddr<=0.7.10 raises ValueError instead of AddrFormatError, bz#1090137

* Mon May 19 2014 Ihar Hrachyshka <ihrachys@redhat.com> 2014.1-17
- Validate CIDR given as ip-prefix in security-group-rule-create, bz#1090137

* Fri May 16 2014 Ihar Hrachyshka <ihrachys@redhat.com> 2014.1-16
- Fixed neutron-server startup due to duplicate options

* Thu May 15 2014 Ihar Hrachyshka <ihrachys@redhat.com> 2014.1-15
- Make neutron-vpn-agent read fwaas_driver.ini, bz#1098121

* Tue Apr 29 2014 Ihar Hrachyshka <ihrachys@redhat.com> 2014.1-14
- Removed signing_dir from neutron-dist.conf, again (bz#1050842)

* Wed Apr 23 2014 Ihar Hrachyshka <ihrachys@redhat.com> 2014.1-13
- Removed obsolete setup scripts

* Wed Apr 23 2014 Ihar Hrachyshka <ihrachys@redhat.com> 2014.1-12
- Removed signing_dir from neutron.conf

* Tue Apr 22 2014 Ihar Hrachyshka <ihrachys@redhat.com> 2014.1-11
- Pin python-novaclient dependency to >= 2.17.0

* Fri Apr 18 2014 Pádraig Brady <pbrady@redhat.com> - 2014.1-10
- Remove uneeded dep on python-keystone

* Fri Apr 18 2014 Ihar Hrachyshka <ihrachys@redhat.com> 2014.1-7
- Require python-novaclient (used for Nova notifications)

* Fri Apr 18 2014 Ihar Hrachyshka <ihrachys@redhat.com> 2014.1-6
- We no longer specify notification_driver in neutron-dist.conf

* Fri Apr 18 2014 Ihar Hrachyshka <ihrachys@redhat.com> 2014.1-5
- Move api-paste.ini to /usr to make sure new values are applied on upgrade

* Fri Apr 18 2014 Terry Wilson <twilson@redhat.com> - 2014.1-4
- Rename nicira plugin to vmware

* Fri Apr 18 2014 Ihar Hrachyshka <ihrachys@redhat.com> 2014.1-3
- Clean up neutron-dist.conf to reflect identical upstream defaults

* Fri Apr 18 2014 Ihar Hrachyshka <ihrachys@redhat.com> 2014.1-2
- Set use_stderr = False to avoid duplicate logging for stderr

* Fri Apr 18 2014 Ihar Hrachyshka <ihrachys@redhat.com> 2014.1-1
- Update to upstream 2014.1

* Tue Apr 15 2014 Miguel Ángel Ajo <majopela@redhat.com> -2014.1-0.19.rc2
- Include the systemd readiness notification patch

* Tue Apr 15 2014 Pádraig Brady <pbrady@redhat.com> - 2014.1-0.18.rc2
- Add missing dependency on python-oslo-rootwrap

* Fri Apr 11 2014 Miguel Angel Ajo <mangelajo@redhat.com> 2014.1-0.17.rc2
- Update to upstream 2014.1.rc2

* Fri Apr 11 2014 Miguel Ángel Ajo <majopela@redhat.com> 2014.1-0.16.rc1
- Use rabbitmq by default

* Thu Apr 10 2014 Miguel Ángel Ajo <majopela@redhat.com> 2014.1-0.15.rc1
- Removes the python-pyudev dependency, bz#1053001

* Thu Apr 10 2014 Ihar Hrachyshka <ihrachys@redhat.com> 2014.1-0.14.rc1
- Remove signing_dir from neutron-dist.conf, bz#1050842

* Fri Apr 04 2014 Pádraig Brady <pbrady@redhat.com> - 2014.1-0.13.rc1
- Fix startup issue due to invalid group permissions, bz#1080560
- Remove runtime dependency on python-pbr

* Wed Apr 02 2014 Terry Wilson <twilson@redhat.com> 2014.1-0.9.rc1
- Update to upstream 2014.1.rc1
- Remove python-psutil requires

* Wed Mar 19 2014 Miguel Ángel Ajo <majopela@redhat.com> - 2014.1.b3-8
- Create agents table when ML2 core_plugin is used
 
* Tue Mar 11 2014 Miguel Ángel Ajo <majopela@redhat.com> - 2014.1.b3-7
- Fixed a broken dependency/typo lxaml -> lxml
- Enforcing python-six >= 1.4.1 at least

* Fri Mar 07 2014 Miguel Ángel Ajo <majopela@redhat.com> - 2014.1.b3-6
- Update to icehouse milestone 3
- Add neutron-dhcp-agent dependency bz#1019487
- Remove nicira plugin, renamed vmware-nsx to vmware bz#1058995
- Add openstack-neutron-ibm plugin
- Add openstack-neutron-ofagent plugin from ryu project

* Tue Feb 04 2014 Pádraig Brady <pbrady@redhat.com> - 2014.1.b2-5
- Fix missing dependency on python-stevedore

* Tue Feb 04 2014 Pádraig Brady <pbrady@redhat.com> - 2014.1.b2-4
- Fix exception on systems with dnsmasq < 2.59

* Mon Jan 27 2014 Terry Wilson <twilson@redhat.com> - 2014.1.b2-3
- Update to icehouse milestone 2

* Tue Jan 07 2014 Terry Wilson <twilson@redhat.com> - 2014.1.b1-2
- Add python-psutil requirement for openvswitch agent, bz#1049235

* Mon Dec 23 2013 Pádraig Brady <pbrady@redhat.com> - 2014.1.b1-1
- Update to icehouse milestone 1

* Wed Dec 18 2013 Pádraig Brady <pbrady@redhat.com> - 2013.2.1-1
- Update to Havana stable release 2013.2.1

* Fri Dec 13 2013 Terry Wilson <twilson@redhat.com> - 2013.2-13
- QPID fixes from oslo-incubator, bz#1038711, bz#1038717
- Remove dnsmasq version warning, bz#997961
- Ensure that disabled services are properly handled on upgrade, bz#1040704

* Mon Dec 09 2013 Terry Wilson <twilson@redhat.com> - 2013.2-12
- Add vpnaas/fwaas configs to init scripts, bz#1032450
- Pass neutron rootwrap.conf in sudoers.d/neutron, bz#984097

* Wed Dec 04 2013 Terry Wilson <twilson@redhat.com> - 2013.2-11
- Add missing debug and vpnaas rootwrap filters, bz#1034207

* Mon Dec 02 2013 Terry Wilson <twilson@redhat.com> - 2013.2-10
- Replace quantum references in neutron-dist.conf

* Tue Nov 19 2013 Pádraig Brady <pbrady@redhat.com> - 2013.2-9
- Fix dependency on parallel installed python-jinja2-26

* Tue Nov 19 2013 Pádraig Brady <pbrady@redhat.com> - 2013.2-8
- Depend on python-webob1.2 rather than deprecated python-webob1.0

* Wed Nov 13 2013 Terry Wilson <twilson@redhat.com> - 2013.2-7
- Add dnsmasq-utils dependency to openstack-neutron

* Wed Nov 13 2013 Pádraig Brady <pbrady@redhat.com> - 2013.2-6
- Fix jinja2 import in openstack-neutron-vpn-agent

* Thu Nov 07 2013 Terry Wilson <twilson@redhat.com> - 2013.2-5
- Update deps for python-{babel,keystoneclient,oslo-config}

* Wed Oct 30 2013 Terry Wilson <twilson@redaht.com> - 2013.2-4
- Better support for upgrading from grizzly to havana

* Thu Oct 24 2013 Terry Wilson <twilson@redhat.com> - 2013.2-3
- Fix previous neutron-ovs-cleanup fix

* Thu Oct 24 2013 Terry Wilson <twilson@redhat.com> - 2013.2-2
- Ensure that neutron-ovs-cleanup completes before exiting (rhbz#1010941)

* Fri Oct 18 2013 Pádraig Brady <pbrady@redhat.com> - 2013.2-1
- Update to havana GA

* Thu Oct 10 2013 Terry Wilson <twilson@redhat.com> - 2013.2-0.12.rc1
- Update to havana rc1

* Wed Oct  2 2013 Terry Wilson <twilson@redhat.com> - 2013.2-0.11.b3
- Add python-jinja2 requires to VPN agent
- Ad missing services for VPN and metering agent

* Thu Sep 26 2013 Terry Wilson <twilson@redhat.com> - 2013.2-0.10.b3
- Add support for neutron-dist.conf

* Tue Sep 17 2013 Pádraig Brady <pbrady@redhat.com> - 2013.2-0.9.b3
- Fix typo in openstack-neutron-meetering-agent package name
- Register all agent services with chkconfig during installation

* Mon Sep 09 2013 Terry Wilson <twilson@rehdat.com> - 2013.2-0.4.b3
- Update to havana milestone 3 release

* Thu Jul 25 2013 Terry Wilson <twilson@redhat.com> - 2013.2-0.3.b2
- Update to havana milestone 2 release
- Rename quantum to neutron

* Mon Jun 17 2013 Terry Wilson <twilson@redhat.com> - 2013.2-0.2.b1
- Update to havana milestone 1 release

* Fri Jun 07 2013 Terry Wilson <twilson@redhat.com> - 2013.1.2-1
- Update to grizzly 2013.1.2 release

* Sun May 26 2013 Gary Kotton <gkotton@redhat.com> - 2013.1.1-6
- Fixes rootwarp path

* Fri May 24 2013 Pádraig Brady <P@draigBrady.com> - 2013.1.1-5
- Fix inclusion of db migrations

* Wed May 22 2013 Gary Kotton <gkotton@redhat.com> - 2013.1.1-3
- Updates to work with namespaces
- Fix kill-metadata rootwrap filter

* Mon May 13 2013 Gary Kotton <gkotton@redhat.com> - 2013.1.1-2
- Update to grizzly stable release 2013.1.1
- Update install scripts to configure security groups
- Update install scripts to remove virtual interface configurations

* Mon Apr 29 2013 Pádraig Brady <pbrady@redhat.com> 2013.1-3
- Fix quantum-ovs-cleanup.init to reference the correct config files

* Thu Apr  4 2013 Gary Kotton <gkotton@redhat.com> - 2013.1-1
- Update to grizzly release

* Thu Apr  4 2013 Gary Kotton <gkotton@redhat.com> - 2013.1-0.7.rc3
- Update to grizzly rc3
- Update rootwrap (bug 947793)
- Update l3-agent-setup to support qpid (bug 947532)
- Update l3-agent-setup to support metadata-agent credentials
- Update keystone authentication details (bug 947776)

* Tue Mar 26 2013 Terry Wilson <twilson@redhat.com> - 2013.1-0.6.rc2
- Update to grizzly rc2

* Tue Mar 12 2013 Pádraig Brady <P@draigBrady.Com> - 2013.1-0.5.g3
- Relax the dependency requirements on sqlalchemy

* Mon Feb 25 2013 Robert Kukura <rkukura@redhat.com> - 2013.1-0.4.g3
- Update to grizzly milestone 3
- Add brocade, hyperv, midonet, and plumgrid plugins as sub-packages
- Remove cisco files that were eliminated
- Add quantum-check-nvp-config
- Include patch for https://code.launchpad.net/bugs/1132889
- Require python-oslo-config
- Require compatible version of python-sqlalchemy
- Various spec file improvements

* Thu Feb 14 2013 Robert Kukura <rkukura@redhat.com> - 2013.1-0.3.g2
- Update to grizzly milestone 2
- Add quantum-db-manage, quantum-metadata-agent,
  quantum-ns-metadata-proxy, quantum-ovs-cleanup, and
  quantum-usage-audit executables
- Add systemd units for quantum-metadata-agent and quantum-ovs-cleanup
- Fix /etc/quantum/policy.json permissions (bug 877600)
- Require dnsmasq (bug 890041)
- Add the version info file
- Remove python-lxml dependency
- Add python-alembic dependency

* Thu Feb 14 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2013.1-0.2.g1
- Rebuilt for https://fedoraproject.org/wiki/Fedora_19_Mass_Rebuild

* Wed Jan 23 2013 Martin Magr <mmagr@redhat.com> - 2012.2.1-1
- Added python-keystone requirement

* Wed Dec  5 2012 Robert Kukura <rkukura@redhat.com> - 2013.1-0.1.g1
- Update to grizzly milestone 1
- Require python-quantumclient >= 1:2.1.10
- Remove unneeded rpc control_exchange patch
- Add bigswitch plugin as sub-package
- Work around bigswitch conf file missing from setup.py

* Mon Dec  3 2012 Robert Kukura <rkukura@redhat.com> - 2012.2.1-1
- Update to folsom stable 2012.2.1
- Add upstream patch: Fix rpc control_exchange regression.
- Remove workaround for missing l3_agent.ini

* Thu Nov 01 2012 Alan Pevec <apevec@redhat.com> 2012.2-2
- l3_agent not disabling namespace use lp#1060559

* Fri Sep 28 2012 Robert Kukura <rkukura@redhat.com> - 2012.2-1
- Update to folsom final
- Require python-quantumclient >= 1:2.1.1

* Tue Aug 21 2012 Robert Kukura <rkukura@redhat.com> - 2012.1-8
- fix database config generated by install scripts (#847785)

* Wed Jul 25 2012 Robert Kukura <rkukura@redhat.com> - 2012.1-6
- Update to 20120715 essex stable branch snapshot

* Mon May 28 2012 Pádraig Brady <P@draigBrady.com> - 2012.1-5
- Fix helper scripts to use the always available openstack-config util

* Mon May 07 2012 Pádraig Brady <P@draigBrady.com> - 2012.1-4
- Fix handling of the mysql service in quantum-server-setup

* Tue May 01 2012 Pádraig Brady <P@draigBrady.com> - 2012.1-3
- Start the services later in the boot sequence

* Wed Apr 25 2012 Pádraig Brady <P@draigBrady.com> - 2012.1-2
- Use parallel installed versions of python-routes and python-paste-deploy

* Thu Apr 12 2012 Pádraig Brady <pbrady@redhat.com> - 2012.1-1
- Initial essex release
