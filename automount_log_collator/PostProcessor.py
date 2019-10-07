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

from .Config import Config
from .KeyedReader import KeyedReader
from .KeyedReaderTree import KeyedReaderTree
from .util import bare_hostname, append_and_set_timestamp, timestamp_from_str

class PostProcessor(object):

    def __init__(self, args):
        self._config = Config(args)

    def _get_collated_files(self, host, paths):
        collationdir = self._config.host_collation_dir(host)
        n = len(collationdir)
        for root, dirs, files in os.walk(collationdir):
            for filename in files:
                path = os.path.join(root, filename)[n:]
                if path != '/.collated':
                    if path not in paths:
                        paths[path] = set()
                    paths[path].add(host)

    def _purge_empty_dirs(self):
        for root, dirs, files in os.walk(self._config.localhost_collation_dir(), topdown=False):
            for dirname in dirs:
                dirpath = os.path.join(root, dirname)
                try:
                    os.rmdir(dirpath)
                    print('rmdir %s ' % dirpath)
                except:
                    pass

    @staticmethod
    def timestamp(line):
        """Return just the timestamp from a line in a collated file."""
        return timestamp_from_str(line.split(maxsplit=1)[0])

    def consolidate(self):
        hosts = self._config.collated_hosts()
        all_relpaths = {}
        for host in hosts:
            collationdir = self._config.host_collation_dir(host)
            n = len(collationdir) + 1
            for root, dirs, files in os.walk(collationdir):
                for filename in files:
                    relpath = os.path.join(root, filename)[n:]
                    if relpath not in all_relpaths:
                        all_relpaths[relpath] = []
                    all_relpaths[relpath].append(host)
        for relpath, hosts in all_relpaths.items():
            krt = KeyedReaderTree()
            inpaths = [os.path.join(self._config.host_collation_dir(host), relpath) for host in hosts]
            outpath = os.path.join(self._config.consolidation_dir(), relpath)
            for inpath in inpaths:
                krt.insert(KeyedReader(inpath, self.__class__.timestamp))
            if os.path.exists(outpath):
                krt.insert(KeyedReader(outpath, self.__class__.timestamp))
            os.makedirs(os.path.dirname(outpath), exist_ok=True)
            outpathnew = '%s.new' % outpath
            with open(outpathnew, 'w') as f:
                for line in krt.lines():
                    f.write(line)
            os.rename(outpathnew, outpath)
            # set the timestamp according to the last key
            t = krt.lastkey.int_timestamp
            os.utime(outpath, (t, t))
        self._finalize_consolidated()

    def _finalize_consolidated(self):
        """Ensure the collated files don't get consolidated again, by moving them."""
        hosts = self._config.collated_hosts()
        all_relpaths = {}
        for host in hosts:
            collationdir = self._config.host_collation_dir(host)
            n = len(collationdir) + 1
            for root, dirs, files in os.walk(collationdir, topdown=False):
                for filename in files:
                    relpath = os.path.join(root, filename)[n:]
                    inpath = os.path.join(collationdir, relpath)
                    outpath = os.path.join(self._config.consolidation_dir(host), relpath)
                    os.makedirs(os.path.dirname(outpath), exist_ok=True)
                    if not os.path.exists(outpath):
                        os.rename(inpath, outpath)
                    else:
                        append_and_set_timestamp(inpath, outpath)
                        os.remove(inpath)
                # remove all the directories, which should be empty now
                # if not, it's because someone else is busy writing here,
                # so ignore that for now, and we'll pick it up next time
                try:
                    os.rmdir(root)
                except OSError:
                    pass
