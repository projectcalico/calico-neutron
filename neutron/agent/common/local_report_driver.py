# Copyright 2015 Mirantis Inc.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

import datetime
import os
import time

from neutron.openstack.common.gettextutils import _LE
from neutron.openstack.common import jsonutils
from neutron.openstack.common import log as logging

LOG = logging.getLogger(__name__)


class NoopDriver(object):
    def __init__(self, cfg, filename):
        pass

    def log_event(self, ev_type, data):
        pass


class ReportDriver(object):
    def __init__(self, cfg, filename):
        self.filename = cfg.AGENT.local_report_path + filename

    def _process_update(self, ev_type, existing, new):
        result = existing.copy()
        result.update(new)
        # handle 'Since' field separately as it is overwritten (deleted)
        # with new data
        if ev_type in existing:
            result[ev_type]['Since'] = existing[ev_type].get('Since')
        # updating 'Since' field
        if (ev_type not in existing or
            new[ev_type].get('Status') != existing[ev_type].get('Status')):
            ts = time.time()
            result[ev_type]['Since'] = (datetime.datetime.fromtimestamp(ts).
                                        strftime('%Y-%m-%d %H:%M:%S'))
        return result

    def log_event(self, ev_type, data):
        ts = time.time()
        meta = {ev_type:
                {'Pid': os.getpid(),
                 'Timestamp': ts,
                 'Date': (datetime.datetime.fromtimestamp(ts).
                         strftime('%Y-%m-%d %H:%M:%S')),
                 }
                }
        meta[ev_type].update(data)

        existing = meta.copy()
        try:
            with open(self.filename, 'r') as f:
                str = f.read() or '{}'
                existing = jsonutils.loads(str)
        except Exception:
            LOG.exception(_LE("Failed reading local report."))

        try:
            new_data = self._process_update(ev_type, existing, meta)
            with open(self.filename, 'w') as f:
                f.write(jsonutils.dumps(new_data,
                                        indent=4, separators=(',', ': ')))
        except Exception:
            LOG.exception(_LE("Failed writing local report."))
        LOG.debug("Done reporting state to local file for %s event", ev_type)
