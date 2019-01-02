"""N-dimensional CSV writer

See :doc:`format` for format specs
"""
import io
import csv
import pandas
import pshell as sh
import xarray
from .proper_unstack import proper_unstack


def write_csv(array, path_or_buf=None):
    """Write an n-dimensional array to an NDCSV file.

    Any number of dimensions are supported. If the array has more than two
    dimensions, all dimensions beyond the first are automatically stacked
    together on the columns of the CSV file; if you want to stack dimensions on
    the rows you'll need to manually invoke :meth:`xarray.DataArray.stack`
    beforehand.

    This function is conceptually similar to :meth:`pandas.DataFrame.to_csv`,
    except that none of the many configuration settings is made available to
    the end user, in order to ensure consistency in the output file.

    :param array:
        One of:

        - :class:`xarray.DataArray`
        - :class:`pandas.Series`
        - :class:`pandas.DataFrame`

    :param path_or_buf:
        One of:

        - .csv file path
        - .csv.gz / .csv.bz2 / .csv.xz file path (the compression algorithm
          is inferred automatically)
        - file-like object open for writing
        - None (the result is returned as a string)
    """
    if path_or_buf is None:
        buf = io.StringIO()
        write_csv(array, buf)
        return buf.getvalue()

    if isinstance(path_or_buf, str):
        # Automatically detect .csv or .csv.gz extension
        with sh.open(path_or_buf, 'w') as fh:
            write_csv(array, fh)
        return

    if isinstance(array, xarray.DataArray):
        _write_csv_dataarray(array, path_or_buf)
    elif isinstance(array, (pandas.Series, pandas.DataFrame)):
        _write_csv_pandas(array, path_or_buf)
    else:
        raise TypeError('Input data is not a xarray.DataArray, pandas.Series '
                        'or pandas.DataFrame')


def _write_csv_dataarray(array, buf):
    """Write :class:`xarray.DataArray` to buffer
    """
    if array.ndim == 0:
        # 0D (scalar) array
        buf.write('%s\n' % array.values)
        return

    # Keep track of non-index coordinates
    # Note that scalar (a-dimensional) coords are silently discarded
    coord_renames = {}
    for k, v in array.coords.items():
        if len(v.dims) > 1:
            raise ValueError("Multi-dimensional coord '%s' is not supported "
                             "by the NDCSV format" % k)
        if len(v.dims) == 1 and v.dims[0] != k:
            coord_renames[k] = '%s (%s)' % (k, v.dims[0])
    array = array.rename(coord_renames)

    if array.ndim > 2:
        # Automatically stack dims beyond the first.
        # In the case where there's already a MultiIndex on a dim beyond
        # the first, first unstack them and then stack them again back all
        # together.
        for dim in array.dims[1:]:
            if isinstance(array.get_index(dim), pandas.MultiIndex):
                # Note: unstacked dims end up on the right
                array = proper_unstack(array, dim)
        # The __columns__ label is completely arbitrary and we're going
        # to lose it in a few moments when dumping to CSV.
        array = array.stack(__columns__=array.dims[1:])

    # non-index coords are lost when converting to pandas.
    # Incorporate them into the MultiIndex
    for dim in array.dims:
        if isinstance(array.coords[dim].to_index(), pandas.MultiIndex):
            array = array.reset_index(dim)
        elif dim not in array.coords:
            # Force default RangeIndex
            array.coords[dim] = array.coords[dim]
        if list(array[dim].coords) != [dim]:
            array = array.set_index({dim: list(array[dim].coords)})

    _write_csv_pandas(array.to_pandas(), buf)


def _write_csv_pandas(array, buf):
    """Write :class:`pandas.Series` or :class:`pandas.DataFrame` to buffer
    """
    # Raise ValueError if there's empty strings in the header
    _check_empty_index(array.index)
    if array.ndim > 1:
        _check_empty_index(array.columns)

    writer = csv.writer(buf, lineterminator='\n')
    if array.index.name is None:
        array.index.name = 'dim_0'

    if array.ndim == 1:
        # pandas.Series. Write header by hand.
        writer.writerow(list(array.index.names) + [''])
        # First element is empty
        if array.iloc[0] == '':
            # An empty cell would confuse read_csv() below. Make it explicit.
            array.iloc[0] = 'nan'
            na_rep = 'nan'
        elif pandas.isnull(array.iloc[0]):
            na_rep = 'nan'
        else:
            # Keep the output CSV as clean as possible
            na_rep = ''
        array.to_csv(buf, header=None, na_rep=na_rep)
    elif isinstance(array.columns, pandas.MultiIndex):
        # pandas.DataFrame with a MultiIndex on the columns.
        # Simplest case - works out of the box with Pandas!
        array.to_csv(buf)
    else:
        # pandas.DataFrame without MultiIndex on the columns.
        # Write header by hand.
        if array.columns.name is None:
            array.columns.name = 'dim_1'
        header_cols = [array.columns.name]
        if len(array.index.names) > 1:
            header_cols += [''] * (len(array.index.names) - 1)
        header_cols += array.columns.values.tolist()
        writer.writerow(header_cols)
        writer.writerow(list(array.index.names) + [''] * len(array.columns))
        array.to_csv(buf, header=None)


def _check_empty_index(idx):
    """Check for empty strings and NaNs in pandas.Index

    :param pandas.Index idx:
        Series.index, DataFrame.index, or DataFrame.columns.
    :raises ValueError:
        If one or more cells of the index are empty strings or NaN
    """
    if isinstance(idx, pandas.MultiIndex):
        for level, label in zip(idx.levels, idx.labels):
            # A MultiIndex with NaNs will have a levels and -1 labels
            # In this example, x = [NaN, 1.0] y = [0, 1]
            # MultiIndex(levels=[[1.0], [0, 1]],
            #            labels=[[-1, -1, 0, 0], [0, 1, 0, 1]],
            #            names=['x', 'y'])
            if (label < 0).any():
                raise ValueError('NaN in index')
            # Check for empty strings
            _check_empty_index(level)
    else:
        if (idx.dtype.kind in 'OU'  # Object or Unicode
                and pandas.Series(idx.str.contains('^$')).fillna(False).any()):
            raise ValueError('Empty string in index')
        if pandas.isnull(idx).any():
            raise ValueError('NaN in index')
