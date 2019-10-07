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

from .util import bare_hostname

class Collator(object):
    def __init__(self, config):
        self._config = config
        self._hostname = bare_hostname()

    def _outpath(self, path):
        return os.path.normpath(os.path.join(self._config.localhost_collation_dir(), path[1:]))

    def mount(self, timestamp, path):
        outpath = self._outpath(path)
        if not os.path.exists(outpath):
            os.makedirs(os.path.dirname(outpath), exist_ok=True)
        with open(outpath, 'a') as outf:
            outf.write('%s %s %s %s\n' % (timestamp.strftime('%Y%m%d-%H:%M:%S'), self._hostname, path, 'mount'))
        t = timestamp.int_timestamp
        os.utime(outpath, (t, t))

    def unmount(self, timestamp, path):
        outpath = self._outpath(path)
        if not os.path.exists(outpath):
            os.makedirs(os.path.dirname(outpath), exist_ok=True)
        with open(outpath, 'a') as outf:
            outf.write('%s %s %s %s\n' % (timestamp.strftime('%Y%m%d-%H:%M:%S'), self._hostname, path, 'unmount'))
        t = timestamp.int_timestamp
        os.utime(outpath, (t, t))
