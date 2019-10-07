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
import pendulum
import re
import sys

class Reader(object):
    def __init__(self, logpath, compressed, logfile_dt):
        self._compressed = compressed
        self._logfile_dt = logfile_dt
        self._logpath = logpath

    def collate_to(self, collator):
        loglineRE = re.compile(r"""^(\S+\s+\d+\s+\d+:\d+:\d+)\s+\S+\s+\S+\s+(\S+)\s+(.*)$""")
        if self._compressed:
            logf = gzip.open(self._logpath, 'r')
        else:
            logf = open(self._logpath, 'r')
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
                        timestamp_year = self._logfile_dt.year - 1 if timestamp_s.startswith('Dec') and self._logfile_dt.month == 1 else self._logfile_dt.year
                        timestamp = pendulum.parse('%d %s' % (timestamp_year, timestamp_s), tz=pendulum.now().timezone, strict=False)
                        action = m.group(2)
                        path = m.group(3)
                        if path.startswith('/'):
                            if action == 'mounted':
                                collator.mount(timestamp, path)
                            elif action == 'expired':
                                collator.unmount(timestamp, path)
                    else:
                        sys.stderr.write('warning: ignoring badly formatted line at %s:%d\n' % (self._logpath, loglineno))
                except UnicodeDecodeError:
                    sys.stderr.write('warning: ignoring badly encoded line at %s:%d\n' % (self._logpath, loglineno))
        except:
            sys.stderr.write('failed at %s:%d\n' % (self._logpath, loglineno))
            raise
        finally:
            logf.close()
