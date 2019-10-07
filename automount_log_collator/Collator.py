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

from .util import bare_hostname, duration_str, timestamp_str, timestamp_from_str

class Collator(object):
    def __init__(self, config):
        self._config = config
        self._hostname = bare_hostname()
        self._last_collation = None
        self._last_path = None
        self._mounts = {}
        self._load()

    def _load(self):
        # last collation timestamp
        try:
            with open(self._config.last_collation_file) as f:
                self._last_collation = timestamp_from_str(f.read())
                print('last collation at', timestamp_str(self._last_collation))
        except (IOError, ValueError):
            pass

        # active mounts
        cdir = self._config.localhost_collation_dir()
        cdir_len = len(cdir)
        for root, dirs, files in os.walk(cdir):
            for filename in files:
                fpath = os.path.join(root, filename)[cdir_len:]

    def _save(self):
        # last collation timestamp
        with open(self._config.last_collation_file, 'w') as f:
            f.write('%s\n' % timestamp_str(self._last_collation))

        # active mounts
        for path, t0 in self._mounts.items():
            fpath = os.path.join(self._config.localhost_collation_dir(active=True), path[1:])
            os.makedirs(os.path.dirname(fpath), exist_ok=True)
            with open(fpath, 'w') as f:
                f.write('%s\n' % timestamp_str(t0))

    def _outpath(self, path):
        return os.path.normpath(os.path.join(self._config.localhost_collation_dir(), path[1:]))

    def pending(self, t0):
        """Return whether records at time t0 are still to be processed"""
        return self._last_collation is None or t0 > self._last_collation

    def _seen(self, t0):
        if self._last_path is None or t0 > self._last_path:
            self._last_path = t0

    def mount(self, t0, path):
        if self.pending(t0):
            print('mount %s at %s' % (path, timestamp_str(t0)))
            self._mounts[path] = t0
            self._seen(t0)

    def unmount(self, t1, path):
        if self.pending(t1):
            print('expire %s at %s' % (path, timestamp_str(t1)))
            if path in self._mounts:
                t0 = self._mounts[path]
                del self._mounts[path]
                d = duration_str(t0, t1)
                outpath = self._outpath(path)
                if not os.path.exists(outpath):
                    os.makedirs(os.path.dirname(outpath), exist_ok=True)
                with open(outpath, 'a') as outf:
                    outf.write('%s %s %s %s\n' % (timestamp_str(t1), self._hostname, path, d))
                t = t1.int_timestamp
                os.utime(outpath, (t, t))
            else:
                sys.stderr.write('warning: no mount found for unmount %s at %s\n', (path, timestamp_str(t1)))
            self._seen(t1)

    def finalize(self):
        """Write out all the current mounts"""
        if self._last_path is not None:
            if self._last_collation is None or self._last_path > self._last_collation:
                self._last_collation = self._last_path
        self._save()
