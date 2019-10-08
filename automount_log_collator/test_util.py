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

import unittest

from .util import path_splitall, escape_path, unescape_path

class TestUtil(unittest.TestCase):

    def test_path_splitall(self):
        self.assertEqual(path_splitall('/a/b/c'), ['a','b','c'])
        self.assertEqual(path_splitall('a/b/c'), ['a','b','c'])
        self.assertEqual(path_splitall('/'), [])

    def test_escape_path(self):
        self.assertEqual(escape_path('/a/b/c'), '_a/_b/_c')
        self.assertEqual(escape_path('/a/b/c', True), '/_a/_b/_c')
        self.assertEqual(escape_path('a/b/c'), '_a/_b/_c')

    def test_unescape_path(self):
        self.assertEqual(unescape_path('/_a/_b/_c', False), 'a/b/c')
        self.assertEqual(unescape_path('/_a/_b/_c'), '/a/b/c')
        self.assertEqual(unescape_path('_a/_b/_c'), 'a/b/c')

if __name__ == '__main__':
    unittest.main()
