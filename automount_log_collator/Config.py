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

import os.path
import pytoml as toml
import re
import sys

from .util import bare_hostname, merge_lists

def expand(s):
    return os.path.expanduser(os.path.expandvars(s))

class ConfigError(Exception):

    def __init__(self, filename, msg):
        self.filename = filename
        self.msg = msg

    def __str__(self):
        return('Configuration error %s: %s' % (self.filename, self.msg))

class Config(object):

    def __init__(self, args):
        self._filename = None
        if args.config:
            self._filename = args.config
            if not os.path.exists(self._filename):
                raise ConfigError('%s' % self._filename, 'file not found')
        else:
            attempt_files = [
                os.path.expanduser('~/.automount-log-collator.toml'),
                '/etc/automount-log-collator.toml',
            ]
            for attempt in attempt_files:
                if os.path.exists(attempt):
                    self._filename = attempt
                    break
            if self._filename is None:
                raise ConfigError('', 'none of %s found' % ', '.join(attempt_files))

        with open(self._filename, 'rb') as f:
            try:
                self._config = toml.load(f)
            except toml.TomlError as e:
                raise ConfigError(self._filename, 'TOML error at line %d, %s' % (e.line, e.message))
        self._validate()

    def _validate(self):
        if 'class' in self._config and 'all' in self._config['class']:
            raise ConfigError(self._filename, 'invalid class "all"')

    def collation_dir(self):
        return expand(self._config['collation-dir'])

    def host_collation_dir(self, host=None):
        if host == None:
            host = bare_hostname()
        return os.path.join(expand(self._config['collation-dir']), host)

    def consolidation_dir(self):
        return expand(self._config['consolidation-dir'])

    @property
    def last_collation_file(self):
        return os.path.join(expand(self._config['collation-dir']), '.%s.collated' % bare_hostname())

    @property
    def logdir(self):
        return expand(self._config['log-dir'])
