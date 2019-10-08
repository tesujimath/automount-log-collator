#!/usr/bin/env python
#
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

import argparse
import sys

from automount_log_collator.Config import ConfigError
from automount_log_collator.Merger import Merger
from automount_log_collator.Scanner import Scanner
from automount_log_collator.version import get_version

def main():
    parser = argparse.ArgumentParser(description='collate automount logfiles')
    parser.add_argument('-v', '--verbose', action='store_true', help='verbose output')
    parser.add_argument('-c', '--config', metavar='FILE', help='configuration file')
    parser.add_argument('command', choices=['collate','consolidate','list-files','list-packages','list-excluded','purge-excluded','version'], help='command to run')
    parser.add_argument('args', nargs=argparse.REMAINDER, help='command arguments')
    args = parser.parse_args()

    try:
        if args.command == 'version':
            print('automount-log-collator v%s' % get_version())
        elif args.command == 'consolidate':
            merger = Merger(args)
            merger.merge()
        elif args.command == 'collate':
            scanner = Scanner(args)
            scanner.scan()
    except ConfigError as e:
        sys.stderr.write('%s\n' % e)
        sys.exit(1)

if __name__ == '__main__':
    main()
