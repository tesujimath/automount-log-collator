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

import os
import os.path
import pendulum
import re
import sys

from .Collator import Collator
from .Config import Config
from .Reader import Reader

class Scanner(object):

    def __init__(self, args):
        self._args = args
        self._config = Config(args)
        self._collator = Collator(self._config)

    def _get_last_collation(self):
        timestampRE = re.compile(r"""^(\d\d\d\d)(\d\d)(\d\d)$""")
        try:
            with open(self._config.last_collation_file) as f:
                m = timestampRE.match(f.read())
                if m:
                    return pendulum.DateTime(int(m.group(1)), int(m.group(2)), int(m.group(3)), tzinfo=pendulum.now().timezone)
            return None
        except (IOError, ValueError):
            return None

    def _set_last_collation(self, dt):
        with open(self._config.last_collation_file, 'w') as f:
            f.write('%s\n' % dt.strftime('%Y%m%d'))

    def scan(self):
        last_collation_dt = self._get_last_collation()

        # important to process logfiles in order, so timestamps are preserved
        for entry in sorted(os.listdir(self._config.logdir)):
            automountLogRE = re.compile(r"""^automount(-(\d\d\d\d)(\d\d)(\d\d).gz)?$""")
            m = automountLogRE.match(entry)
            if m:
                entryPath = os.path.join(self._config.logdir, entry)
                if m.group(1):
                    compressed = True
                    logfile_year = int(m.group(2))
                    logfile_month = int(m.group(3))
                    logfile_day = int(m.group(4))
                    logfile_dt = pendulum.DateTime(logfile_year, logfile_month, logfile_day, tzinfo=pendulum.now().timezone)
                else:
                    compressed = False
                    logfile_dt = pendulum.from_timestamp(os.path.getmtime(entryPath), tz=pendulum.now().timezone_name)
                if last_collation_dt is None or last_collation_dt < logfile_dt:
                    reader = Reader(entryPath, compressed, logfile_dt)
                    if self._args.verbose:
                        sys.stdout.write('collating %s\n' % entry)
                    reader.collate_to(self._collator)
                    last_collation_dt = logfile_dt
                    self._set_last_collation(last_collation_dt)
                else:
                    if self._args.verbose:
                        sys.stdout.write('skipping %s\n' % entry)
