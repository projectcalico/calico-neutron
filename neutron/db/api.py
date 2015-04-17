# Copyright 2011 VMware, Inc.
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

import functools
import six
import sys

from oslo.config import cfg
from oslo.db.sqlalchemy import session

from neutron.openstack.common import log as logging

LOG = logging.getLogger(__name__)
_FACADE = None

MAX_RETRIES = 10


def _create_facade_lazily():
    global _FACADE

    if _FACADE is None:
        _FACADE = session.EngineFacade.from_config(cfg.CONF, sqlite_fk=True)

    return _FACADE


def get_engine():
    """Helper method to grab engine."""
    facade = _create_facade_lazily()
    return facade.get_engine()


def get_session(autocommit=True, expire_on_commit=False):
    """Helper method to grab session."""
    facade = _create_facade_lazily()
    return facade.get_session(autocommit=autocommit,
                              expire_on_commit=expire_on_commit)


class RetryRequest(Exception):
    def __init__(self, inner_exc):
        self.inner_exc = inner_exc


def db_retry_on_request(f, max_retries=MAX_RETRIES):
    """Decorator to retry a DB API call if inner code requests so.
    This might be needed if inner code detects that it need to
    restart whole transaction.
    """
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        for attempt in xrange(1, max_retries + 2):
            try:
                LOG.debug("Trying operation "
                          "'%(func_name)s', attempt %(attempt)s",
                          {'func_name': f.__name__,
                           'attempt': attempt})
                return f(*args, **kwargs)
            except RetryRequest as e:
                if attempt >= max_retries + 1:
                    LOG.warn(_("Operation '%(func_name)s' has failed "
                               "after %(attempts)s attempts"),
                             {'func_name': f.__name__,
                              'attempts': attempt})
                    # preserve original stack trace
                    # which is contained in 'e'
                    six.reraise(type(e.inner_exc),
                                e.inner_exc,
                                sys.exc_info()[2])

    return wrapper
