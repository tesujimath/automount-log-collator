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

from .util import ( bare_hostname, duration_str, timestamp_str, timestamp_from_str, purge_empty_dirs,
                    escape_path, unescape_path )

class Collator(object):
    def __init__(self, config, verbose):
        self._config = config
        self._verbose = verbose
        self._hostname = bare_hostname()
        self._last_collation = None
        self._last_path = None
        self._mounts = {}
        self._persisted_mounts = {} # for mounts which were saved in filesystem
        self._dirty = False     # whether we need to cleanup persisted mount directories
        self._load()

    def host_history_path(self, host, path):
        """Return the path to the mount history file."""
        return os.path.join(self._config.host_collation_dir(host), escape_path(path), 'history')

    def _history_path(self, path):
        """Return the path to the mount history file."""
        return self.host_history_path(None, path)

    def host_active_path(self, host, path):
        """Return the path to the active mount file."""
        return os.path.join(self._config.host_collation_dir(host), escape_path(path), 'active')

    def _active_path(self, path):
        """Return the path to the active mount file."""
        return self.host_active_path(None, path)

    def _path_from_mounts_filepath(self, filepath, host=None):
        """Return the path represented by the active or history file."""
        return os.path.dirname(unescape_path(filepath[len(self._config.host_collation_dir(host)):]))

    def _load(self):
        # last collation timestamp
        try:
            with open(self._config.last_collation_file) as f:
                self._last_collation = timestamp_from_str(f.read())
                if self._verbose:
                    sys.stdout.write('last collation at %s\n' % timestamp_str(self._last_collation))
        except (IOError, ValueError):
            pass

        # active mounts
        for root, dirs, files in os.walk(self._config.host_collation_dir()):
            if 'active' in files:
                # read actual file, and path for mount, and its timestamp
                filepath = os.path.join(root, 'active')
                path = self._path_from_mounts_filepath(filepath)
                #if self._verbose:
                #    sys.stdout.write('path from %s is %s\n' % (filepath, path))
                with open(filepath, 'r') as f:
                    for line in f:
                        t0 = timestamp_from_str(line)
                        self._mounts[path] = t0
                        self._persisted_mounts[path] = True
                        if self._verbose:
                            sys.stdout.write('load mount %s at %s\n' % (path, t0))

    def _save(self):
        # last collation timestamp
        with open(self._config.last_collation_file, 'w') as f:
            f.write('%s\n' % timestamp_str(self._last_collation))

        # ensure we don't persist an active mount which is not in fact mounted
        bogus_mounts = {}
        for path in self._mounts:
            if not os.path.ismount(path):
                bogus_mounts[path] = True
        for path in bogus_mounts:
            if self._verbose:
                sys.stdout.write('bogus mount %s, discarding\n' % path)
            self.unmount(pendulum.now(), path)

        # active mounts
        now = pendulum.now().int_timestamp
        for path, t0 in self._mounts.items():
            active_path = self._active_path(path)
            os.makedirs(os.path.dirname(active_path), exist_ok=True)
            with open(active_path, 'w') as f:
                f.write('%s\n' % timestamp_str(t0))
                if self._verbose:
                    sys.stdout.write('save mount %s at %s\n' % (path, t0))
            # set timestamp of collated file to now, to indicate that it is still in use
            history_path = self._history_path(path)
            if not os.path.exists(history_path):
                # create empty file, so we can touch it
                open(history_path, 'a').close()
            os.utime(history_path, (now, now))

    def pending(self, t0):
        """Return whether records at time t0 are still to be processed"""
        return self._last_collation is None or t0 > self._last_collation

    def _seen(self, t0):
        if self._last_path is None or t0 > self._last_path:
            self._last_path = t0

    def mount(self, t0, path):
        if self.pending(t0):
            if self._verbose:
                sys.stdout.write('mount %s at %s\n' % (path, timestamp_str(t0)))
            self._mounts[path] = t0
            self._seen(t0)

    def _resolve_active_mount(self, path):
        # remove that mount is active, and return its timestamp
        #if self._verbose:
        #    sys.stdout.write('remove active mount %s\n' % path)
        t0 = self._mounts[path]
        del self._mounts[path]
        if path in self._persisted_mounts:
            del self._persisted_mounts[path]
            active_path = self._active_path(path)
            if os.path.exists(active_path):
                if self._verbose:
                    sys.stdout.write('remove active mount file %s\n' % path)
                os.remove(active_path)
                self._dirty = True
        return t0

    def unmount(self, t1, path):
        if self.pending(t1):
            if self._verbose:
                sys.stdout.write('expire %s at %s\n' % (path, timestamp_str(t1)))
            if path in self._mounts:
                t0 = self._resolve_active_mount(path)
                d = duration_str(t0, t1)
            else:
                d = 'unknown'
                if self._verbose:
                    sys.stderr.write('warning: no mount found for unmount %s at %s\n' % (path, timestamp_str(t1)))
            history_path = self._history_path(path)
            if not os.path.exists(history_path):
                os.makedirs(os.path.dirname(history_path), exist_ok=True)
            with open(history_path, 'a') as outf:
                outf.write('%s %s %s\n' % (timestamp_str(t1), self._hostname, d))
            t = t1.int_timestamp
            os.utime(history_path, (t, t))

            self._seen(t1)

    def purge_empty_dirs(self, host=None):
        purge_empty_dirs(self._config.host_collation_dir(host))

    def finalize(self):
        """Write out all the current mounts"""
        if self._last_path is not None:
            if self._last_collation is None or self._last_path > self._last_collation:
                self._last_collation = self._last_path
            self._save()
        # remove any empty directories among the persisted mounts, if we deleted anything
        if self._dirty:
            self.purge_empty_dirs()

    def hosts(self):
        """Return list of hosts which have collations."""
        return [ x for x in os.listdir(self._config.collation_dir())
                 if not x.startswith('.') ]

    def paths(self, host):
        """Return collated paths for host."""
        for root, dirs, files in os.walk(self._config.host_collation_dir(host)):
            if 'active' in files or 'history' in files:
                filepath = os.path.join(root, 'history')
                yield self._path_from_mounts_filepath(filepath, host)
