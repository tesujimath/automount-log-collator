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

class KeyedReader(object):

    def __init__(self, path, keyfn):
        self._path = path
        self._f = open(path, 'r')
        self._keyfn = keyfn
        self.next()

    def __str__(self):
        return 'KeyedReader(%s)' % self._path

    def next(self):
        if self._f is not None:
            self.line = self._f.readline()
            if self.line != '':
                self.key = self._keyfn(self.line)
            else:
                self.key = None
                self._f.close()
                self._f = None
