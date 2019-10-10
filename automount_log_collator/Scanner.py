# Copyright (c) 2019 Simon Guest
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import gzip
import os
import os.path
import pendulum
import re
import sys

from .Collator import Collator
from .Config import Config
from .util import timestamp_str

class Scanner(object):

    def __init__(self, args):
        self._args = args
        self._config = Config(args)
        self._collator = Collator(self._config, self._args.verbose)

    def _collate_if_pending(self, logpath, logfile_dt, compressed):
        # skip processing of files we've already seen
        if not self._collator.pending(logfile_dt):
            if self._args.verbose:
                sys.stdout.write('skipping %s, timestamp %s\n' % (logpath, timestamp_str(logfile_dt)))
            return

        if self._args.verbose:
            sys.stdout.write('collating %s\n' % logpath)

        loglineRE = re.compile(r"""^(\S+\s+\d+\s+\d+:\d+:\d+)\s+\S+\s+\S+\s+(\S+)\s+(/\S*)$""")
        if compressed:
            logf = gzip.open(logpath, 'rt')
        else:
            logf = open(logpath, 'r')
        loglineno = 0
        try:
            for logline in logf:
                try:
                    loglineno += 1
                    m = loglineRE.match(logline)
                    if m:
                        # infer the year for the timestamp, which is usually the same as the logfile year,
                        # except when we roll over from Dec to Jan
                        timestamp_s = m.group(1)
                        timestamp_year = logfile_dt.year - 1 if timestamp_s.startswith('Dec') and logfile_dt.month == 1 else logfile_dt.year
                        timestamp = pendulum.parse('%d %s' % (timestamp_year, timestamp_s), tz=pendulum.now().timezone, strict=False)
                        action = m.group(2)
                        path = m.group(3)
                        if self._collator.pending(logfile_dt):
                            if action == 'mounted':
                                self._collator.mount(timestamp, path)
                            elif action == 'expired':
                                self._collator.unmount(timestamp, path)
                except UnicodeDecodeError:
                    sys.stderr.write('warning: ignoring badly encoded line at %s:%d\n' % (logpath, loglineno))
        except:
            sys.stderr.write('failed at %s:%d\n' % (logpath, loglineno))
            raise
        finally:
            logf.close()

    def scan(self):
        # important to process log-rotated logfiles in order, so timestamps are preserved
        for entry in sorted(os.listdir(self._config.logdir)):
            automountLogRE = re.compile(r"""^automount-(\d\d\d\d)(\d\d)(\d\d).gz$""")
            m = automountLogRE.match(entry)
            if m:
                logpath = os.path.join(self._config.logdir, entry)
                logfile_year = int(m.group(1))
                logfile_month = int(m.group(2))
                logfile_day = int(m.group(3))
                logfile_dt = pendulum.DateTime(logfile_year, logfile_month, logfile_day, tzinfo=pendulum.now().timezone)
                self._collate_if_pending(logpath, logfile_dt, compressed=True)

        # finally look at the uncompressed logfile
        logpath = os.path.join(self._config.logdir, 'automount')
        if os.path.exists(logpath):
            logfile_dt = pendulum.from_timestamp(os.path.getmtime(logpath), tz=pendulum.now().timezone_name)
            self._collate_if_pending(logpath, logfile_dt, compressed=False)

        self._collator.finalize()
