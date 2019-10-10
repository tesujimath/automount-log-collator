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
import sys

from .Collator import Collator
from .Config import Config
from .KeyedReader import KeyedReader
from .KeyedReaderTree import KeyedReaderTree
from .util import ( bare_hostname, append_and_set_timestamp, timestamp_from_str, relativize_path,
                    force_makedirs )

class Merger(object):

    def __init__(self, args):
        self._config = Config(args)
        self._collator = Collator(self._config, args.verbose)
        self._verbose = args.verbose

    @staticmethod
    def timestamp(line):
        """Return just the timestamp from a line in a collated file."""
        return timestamp_from_str(line.split(maxsplit=1)[0])

    def _consolidation_path(self, path):
        """Return the path to the consolidated file."""
        return os.path.join(self._config.consolidation_dir(), relativize_path(path))

    def merge(self):
        all_paths = {}
        for host in self._collator.hosts():
            if self._verbose:
                sys.stdout.write('merge checking host %s\n' % host)
            for path in self._collator.paths(host):
                if path not in all_paths:
                    all_paths[path] = []
                if self._verbose:
                    sys.stdout.write('merge path %s for host %s\n' % (path, host))
                all_paths[path].append(host)
        for path, hosts in all_paths.items():
            krt = KeyedReaderTree()
            outpath = os.path.join(self._config.consolidation_dir(), relativize_path(path))
            for history_path in [ self._collator.host_history_path(host, path) for host in hosts ]:
                if os.path.isfile(history_path):
                    if self._verbose:
                        sys.stdout.write('history_path %s\n' % history_path)
                    krt.insert(KeyedReader(history_path, self.__class__.timestamp))
            if os.path.isfile(outpath):
                krt.insert(KeyedReader(outpath, self.__class__.timestamp))
            if krt.n > 0:
                force_makedirs(os.path.dirname(outpath), exist_ok=True, verbose=self._verbose)
                outpathnew = '%s.new' % outpath
                with open(outpathnew, 'w') as f:
                    for line in krt.lines():
                        f.write(line)
                os.rename(outpathnew, outpath)
            # set the timestamp according to the last key, or the active path if that exists
            t0 = krt.lastkey.int_timestamp if krt.lastkey is not None else None
            for host in hosts:
                active_path = self._collator.host_active_path(host, path)
                if os.path.exists(active_path):
                    t = os.stat(active_path).st_mtime
                    if t0 is None or t > t0:
                        t0 = t
            os.utime(outpath, (t0, t0))
        self._finalize_consolidated()

    def _finalize_consolidated(self):
        """Ensure the history files don't get consolidated again, by removing them."""
        for host in self._collator.hosts():
            for path in self._collator.paths(host):
                history_path = self._collator.host_history_path(host, path)
                if os.path.exists(history_path):
                    os.remove(history_path)
            self._collator.purge_empty_dirs(host)
