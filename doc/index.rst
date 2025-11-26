ndcsv: N-Dimensional CSV files for xarray
=========================================

NDCSV is a file format that allows storing N-dimensional labelled arrays
into human-readable CSV files and read them back without needing any
configuration, load hints, or sidecar configuration files.

The fundamental concept is that, unlike :meth:`pandas.DataFrame.to_csv`
and :func:`pandas.read_csv`, reading and writing objects is fully automated
and reversible. One does not need to specify how many rows and/or columns of
header are available - the file format is unambiguous and the library
automatically does the right thing.

The format was designed around `xarray <https://xarray.dev/>`_, so it
supports, out of the box:

- Arrays with any number of dimensions
- Labelled, named indices
- Non-index coordinates

Index
-----

.. toctree::

   format
   dataloss
   installing
   api
   develop
   whats-new

Credits
-------
ndcsv was initially developed internally as ``landg.ndcsv`` by
`Legal & General <http://www.landg.com>`_.
It was open-sourced in 2018.

License
-------
The ndcsv Python module is available under the open source `Apache License`__.

The ndcsv format is patent-free and in the public domain. Anybody
can write an alternative implementation; compatibility with the
Python module is not enforced by law, but strongly encouraged.

__ http://www.apache.org/licenses/LICENSE-2.0.html
