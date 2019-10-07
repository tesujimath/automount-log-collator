automount-log-collator
======================

Automount-log-collator collates the autmounter log files, producing a
summary of what has been mounted and where.

Collation is run on each individual server, and ideally the ``collation-dir`` is
on a fileserver.  A second phase, consolidation, is used to merge all the
separate collated files into a single instance across all servers.
Consolidation is run just once, rather than on each individual server.

Installation
------------

Automount-log-collator is on PyPI, so may be installed using pip, preferably in
a virtualenv.

::

    $ pip install automount-log-collator

Alternatively, automount-log-collator is also on conda-forge.

::

    $ conda install automount-log-collator

Note that automount-log-collator requires Python 3.

Configuration
-------------

See the See the `example configuration file <doc/example-config.toml>`__.


Example Use
-----------

::

    $ automount-log-collator -c example-config.toml collate
    $ automount-log-collator -c example-config.toml consolidate

Notes
-----

Automount-log-collator looks for logfiles in the log directory named
``automount-YYYYMMDD.gz`` or ``automount``.  It therefore processes
the currently active logfile in place.

Once a logfile has been collated, the timestamp of the last collated
entry is recorded in ``<collation-dir>/.<hostname>.collated``, to
avoid repeated collation on subsequent runs.
