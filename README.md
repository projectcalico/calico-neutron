This repository is Project Calico's fork of the OpenStack Neutron project.

Branches containing Calico-related work are generally named
calico\_`TAG` or `DISTRIBUTION`\_`TAG`, where

- `TAG` is the OpenStack version number, such as 2014.2.1

- `DISTRIBUTION` names the distribution that the branch's code aims to
  be installed on, such as "ubuntu" or "rhel7".

calico\_`TAG` branches contain Calico-specific changes to the upstream
OpenStack code.  `DISTRIBUTION`\_`TAG` branches incorporate those code
changes and also contain packaging and metadata as appropriate for the
target distribution.  In some cases (such as Ubuntu) the packaging
branches represent the code changes in a quite different form from the
Git commits that you can see in the related calico\_`TAG` branch;
e.g. as patch files under `debian/patches`.  Therefore, if you're
interested in Calico's changes to OpenStack code, best to look at the
calico\_`TAG` branch; if you're interested in the packaging for a
particular distribution, look at `DISTRIBUTION`\_`TAG`.

The following branches are currently our **active** ones - i.e. the ones
that we actively maintain for installing Calico on the relevant target
distribution:

- calico\_2014.1.3 and ubuntu\_2014.1.3, for installation on Ubuntu
  14.04 (Trusty).

- calico\_2014.1.1 and ubuntu\_precise\_mira\_2014.1.1, for installing
  Calico using Mirantis Fuel 5.1.

- calico\_2014.2.1 and rhel7\_2014.2.1, for installation on Red Hat
  Enterprise Linux 7.

Please do contact us via http://www.projectcalico.org/community/, for
help with rebasing or applying Calico patches to other upstream
releases, or with targeting other distributions.
