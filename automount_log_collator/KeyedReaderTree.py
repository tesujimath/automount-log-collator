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

class KeyedReaderTree(object):
    """A KeyedReaderTree is a binary tree used for merging lines from KeyReader's
    in order of key."""

    def __init__(self, reader=None):
        # Nodes with children have no reader themselves.
        # Also, the left child is filled first, so cannot be None if there is a child.
        self._reader = reader
        self._left = None
        self._right = None
        self._next = self._reader
        self.n = 1 if reader is not None else 0
        self.lastkey = None

    def __str__(self):
        return 'KRT(%d, %s, %s, %s)' % (self.n, self._reader, self._left, self._right)

    def _set_next(self):
        if self._reader is not None:
            if self._reader.key is not None:
                self._next = self._reader
            else:
                self._next = None
        elif self._right is None or self._right.key is None:
            if self._left.key is not None:
                self._next = self._left
            else:
                self._next = None
        elif self._left.key is None:
            self._next = self._right
        else:
            if self._left.key <= self._right.key:
                self._next = self._left
            else:
                self._next = self._right

    @property
    def key(self):
        if self._next is not None:
            return self._next.key
        else:
            return None

    @property
    def line(self):
        if self._next is not None:
            return self._next.line
        else:
            return ''

    def insert(self, reader):
        if self._reader is None and self._left is None and self._right is None:
            self._reader = reader
        elif self._reader is not None:
            self._left = KeyedReaderTree(self._reader)
            self._reader = None
            self.insert(reader)
        elif self._right is None:
            self._right = KeyedReaderTree(reader)
        else:
            if self._left.n < self._right.n:
                self._left.insert(reader)
            else:
                self._right.insert(reader)
        self.n += 1
        self._set_next()

    def lines(self):
        while self.key is not None:
            self.lastkey = self.key
            line = self.line
            yield line
            self.next()

    def next(self):
        if self._next is not None:
            self._next.next()
            self._set_next()

    def write(self, f, level=0):
        if self._reader is not None:
            f.write('%s%s\n' % ('.' * level, self._reader))
        if self._left is not None:
            f.write('%sL\n' % ('.' * level))
            self._left.write(f, level + 1)
        if self._right is not None:
            f.write('%sR\n' % ('.' * level))
            self._right.write(f, level + 1)
