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
import pendulum
import sys

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

def merge_lists(l1, l2):
    return list(set(l1) | set(l2))

def duration_str(t1, t2):
    """String difference between pendulum datetimes."""
    delta = t2 - t1
    d = delta.days
    h = delta.hours
    m = delta.minutes
    if d > 0:
        result = '%dd-%d:%02d' % (d, h, m)
    else:
        result = '%d:%02d' % (h, m)
    return result

def timestamp_str(t0):
    return t0.strftime('%Y%m%d-%H:%M:%S')

def timestamp_from_str(s):
    return pendulum.from_format(s, 'YYYYMMDD-HH:mm:ss', tz=pendulum.now().timezone)

def rmdir_if_empty(dirpath):
    try:
        os.rmdir(dirpath)
    except OSError:
        # non-empty, didn't want to delete it anyway
        pass

def purge_empty_dirs(rootdir):
    for root, dirs, files in os.walk(rootdir, topdown=False):
        for dirname in dirs:
            rmdir_if_empty(os.path.join(root, dirname))
    rmdir_if_empty(rootdir)

def path_splitall(path):
    xs = []
    head = path
    while head != os.sep and head != '':
        head, tail = os.path.split(head)
        if tail != '':
            xs.insert(0, tail)
    return xs

def escape_path(path, abspath=False):
    tail = os.path.join(*['_' + x for x in path_splitall(path)])
    return os.sep + tail if abspath and path.startswith(os.sep) else tail

def unescape_path(path, abspath=True):
    tail = os.path.join(*[x[1:] if x.startswith('_') else x for x in path_splitall(path)])
    return os.sep + tail if abspath and path.startswith(os.sep) else tail

def relativize_path(path):
    return path[1:] if path.startswith(os.sep) else path

def force_makedirs(path, exist_ok=True, verbose=False):
    """If there's a file in the way, delete it."""
    done = False
    while not done:
        try:
            os.makedirs(path, exist_ok=exist_ok)
            done = True
        except FileExistsError as e:
            # last component is a file
            if os.path.isfile(e.filename):
                if verbose:
                    sys.stdout.write('removing file %s to create directory %s\n' % (e.filename, path))
                os.remove(e.filename)
            else:
                raise
        except NotADirectoryError as e:
            # some parent is a file, so look back up to find it, and remove it
            badpath = e.filename
            while not os.path.isfile(badpath):
                badpath = os.path.dirname(badpath)
            if verbose:
                sys.stdout.write('removing file %s to create directory %s\n' % (e.filename, path))
            os.remove(badpath)
