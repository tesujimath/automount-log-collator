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

def bare_hostname():
    """Hostname without domain."""
    return os.uname()[1].split('.')[0]

def append_and_set_timestamp(inpath, outpath):
    with open(inpath, 'r') as inf:
        with open(outpath, 'a') as outf:
            done = False
            bufsize = 104857600 # 10MB at a time
            bytes = inf.read(bufsize)
            while bytes != '':
                outf.write(bytes)
                bytes = inf.read(bufsize)
    t = os.stat(inpath).st_mtime
    os.utime(outpath, (t, t))
