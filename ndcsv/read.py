"""N-dimensional CSV reader

See :doc:`format` for format specs
"""

from __future__ import annotations

import csv
import io
import re
from collections.abc import Hashable
from typing import Any, TextIO, cast

import pandas as pd
import pshell as sh
from xarray import DataArray

from ndcsv.proper_unstack import proper_unstack


def read_csv(path_or_buf: str | TextIO, unstack: bool = True) -> DataArray:
    """Parse an NDCSV file into a :class:`xarray.DataArray`.

    This function is conceptually similar to :func:`pandas.read_csv`, except
    that it only works for files that are strictly formatted according to
    :doc:`format` and, by design, does not offer any of the many config
    switches available in :func:`pandas.read_csv`.

    :param path_or_buf:
        One of:

        - .csv file path
        - .csv.gz / .csv.bz2 / .csv.xz file path (the compression algorithm
          is inferred automatically)
        - file-like object open for reading. It must support rewinding through
          ``seek(0)``.

    :param bool unstack:
        Set to True (the default) to automatically unstack any and all stacked
        dimensions in the output xarray, using first-seen order. Note that this
        differs from :meth:`xarray.DataArray.unstack`, which may occasionally
        use alphabetical order instead.
        All indices must be unique for the unstack to succeed. Non-index coords
        can be duplicated.

        Set to False to return the stacked dimensions as they appear in
        the CSV file.
    :returns:
        :class:`xarray.DataArray`
    """
    if isinstance(path_or_buf, str):
        with sh.open(path_or_buf) as fh:
            return read_csv(cast(TextIO, fh), unstack=unstack)

    xa = _buf_to_xarray(path_or_buf)
    assert xa.ndim in (0, 1, 2)
    # print(f"==== _buf_to_array:\n{xa}")

    xa = _coords_format_conversion(xa)
    assert xa.ndim in (0, 1, 2)
    # print(f"==== _coords_format_conversion:\n{xa}")

    if xa.ndim == 1:
        xa = _unpack(xa, xa.dims[0], unstack)
        # print(f"==== _unpack(dim_0):\n{xa}")
    elif xa.ndim == 2:
        dims = xa.dims
        xa = _unpack(xa, dims[0], unstack)
        # print(f"==== _unpack(dim_0):\n{xa}")
        xa = _unpack(xa, dims[1], unstack)
        # print(f"==== _unpack(dim_1):\n{xa}")

    return xa


def _buf_to_xarray(buf: TextIO) -> DataArray:
    """Step 1 of read_csv().
    Read text buffer object and convert it to a :class:`xarray.DataArray`.

    - the Array always has 0, 1, or 2 dimensions
    - in case of MultiIndex, dims are arbitrarily labelled dim0, dim1
    - coords may be MultiIndexes
    - non-index coords are merged inside the MultiIndex with the label
      `coord name (dim)`
    - coords are auto-converted by Pandas (poorly)
    - bools and datetimes are in string format
    - Anything inside a MultiIndex has dtype=object
    """
    reader = csv.reader(buf)

    # Store header rows (only). Won't read the whole file with csv.reader.
    rows: list[list[str]] = []
    columns: list = []
    indexes: list = []
    num_index_col = None
    num_header_rows = None

    for row in reader:
        # Remove empty cells to the right and whitespaces
        # at beginning and end of every cell
        row = [cell.strip() for cell in row]
        while row[-1] == "":
            del row[-1]

        rows.append(row)

        if len(rows) == 2 and len(rows[0]) == len(rows[1]) - 1:
            # This is a pd.Series
            num_index_col = len(rows[0])
            num_header_rows = 1
            break

        if len(rows) == 3:
            # This is a pd.DataFrame
            # Do we have a MultiIndex on the rows?
            try:
                num_index_col = rows[0].index("") + 1
            except ValueError:
                # No MultiIndex on the rows
                num_index_col = 1

            # Find the first line exactly as long as num_index_col
            if len(rows[1]) == num_index_col:
                num_header_rows = 1
                indexes = rows[1]
                columns = rows[0]
                break

            # Find the first line exactly as long as num_index_col
            if len(rows[2]) == num_index_col:
                num_header_rows = 2
                indexes = rows[2]
                columns = rows[:2]
                break

        if len(rows) >= 3:
            assert num_index_col is not None
            if len(rows[-1]) == num_index_col:
                num_header_rows = len(rows) - 1
                indexes = rows[-1]
                columns = rows[:-1]
                break
    else:
        # Reached end of file
        if len(rows) == 1 and len(rows[0]) == 1:
            # 0-dimensional file
            # Let pd.read_csv() apply its magic type detection
            df = pd.read_csv(
                io.StringIO(rows[0][0]), header=None, float_precision="high"
            )
            return DataArray(df.iloc[0, 0])
        raise ValueError("Malformed N-dimensional CSV")

    # Use pandas to read the whole file
    # This is much faster than csv.reader and also applies pandas
    # automatic type recognition.
    buf.seek(0)
    index_col = 0 if num_index_col == 1 else list(range(num_index_col))
    assert num_header_rows is not None
    header = list(range(num_header_rows))

    # If no MultiIndex on columns and it's not a Series, read_csv should not be
    # passed a header
    if len(header) == 1 and len(indexes) > 0:
        df = pd.read_csv(
            buf,
            index_col=index_col,
            header=None,
            low_memory=False,
            skiprows=2,
            float_precision="high",
        )
        df.index.names = indexes
        df.columns = columns[num_index_col:]
        df.columns.names = [columns[0]]
    else:
        df = pd.read_csv(
            buf,
            index_col=index_col,
            header=header[0] if len(header) == 1 else header,
            low_memory=False,
            float_precision="high",
        )

    if len(indexes) == 0:
        # If originally a Series, squeeze empty df dim
        # Do not use df.squeeze() as it will convert a (1, 1) DataFrame
        # into a scalar, whereas we always want a Series.
        df = df.iloc[:, 0]

    xa = DataArray(df)
    xa.name = None
    return xa


def _coords_format_conversion(xa: DataArray) -> DataArray:
    """Automated format conversion for coords

    For every coord (either inside or outside of a MultiIndex), auto-convert
    to numeric, date, or boolean
    Any MultiIndex objects are unpacked.

    :param xa:
        array whose coords need to be converted
    :returns:
        array with converted coords
    """
    # Unpack any MultiIndexes
    for k, v in list(xa.coords.items()):
        if isinstance(v.to_index(), pd.MultiIndex):
            xa = xa.reset_index(k)

    for k, v in list(xa.coords.items()):
        # Convert numpy array of objects, as loaded by pandas, to array of
        # int, float, etc.
        xa.coords[k] = v.dims, v.values.tolist()
        v_data = xa.coords[k].values
        v_data = _try_to_date(v_data)
        v_data = _try_to_numeric(v_data)
        v_data = _try_to_bool(v_data)
        xa.coords[k] = xa.coords[k].dims, v_data
    return xa


def _try_to_date(x: Any) -> Any:
    """Wrapper around :func:`pandas.to_datetime` that returns
    the input unaltered if it's not a date.
    Don't attempt converting numeric or boolean arrays.
    """
    if x.dtype.kind != "U":  # unicode string
        return x
    try:
        # In case of ambiguity, prefer European format DD/MM/YYYY to the
        # American format MM/DD/YYYY
        return pd.to_datetime(x, dayfirst=True)
    except ValueError:
        return x


def _try_to_numeric(x: Any) -> Any:
    """Wrapper around :func:`pandas.to_numeric` that returns
    the input unaltered if it's a string or another non-numeric type.

    In the use case when some of the elements are not numeric, e.g.
    ``S001,00200,S003``, make sure none are converted. This:

      _try_to_numeric(v)

    is very different from::

      [_try_to_numeric(x) for x in v]
    """
    if x.dtype.kind != "U":  # Unicode string
        return x
    try:
        return pd.to_numeric(x)
    except ValueError:
        return x


_BOOL_MAP = {
    "T": True,
    "Y": True,
    "YES": True,
    "TRUE": True,
    "F": False,
    "N": False,
    "NO": False,
    "FALSE": False,
}


def _try_to_bool(x: Any) -> Any:
    """Attempt converting an array of strings into an array of bools. Return
    the original, unaltered array if any element fails conversion.
    """
    if x.dtype.kind != "U":  # Unicode string
        return x
    try:
        return [_BOOL_MAP[i.upper()] for i in x.tolist()]
    except KeyError:
        return x


def _unpack(xa: DataArray, dim: Hashable, unstack: bool = True) -> DataArray:
    """Deal with MultiIndex and non-index coords

    :param DataArray xa:
        array where all MultiIndex'es have been reset
    :param str dim:
        dim to unstack (dim_0 or dim_1). This function does nothing if
        the dim is not present at all
    :param bool unstack:
        If True, unstack all index dims using first-seen order
    """
    rename_map = {}
    dims = []
    index_coords = []
    nonindex_coords = []

    for k, v in xa.coords.items():
        assert len(v.dims) == 1
        if v.dims[0] == dim:
            # Non-index coords are formatted as `name (dim)`
            m = re.match(r"(.+) \((.+)\)$", str(k))
            if m:
                coord_name, coord_dim = m.group(1), m.group(2)
                # Non-index coordinate
                rename_map[k] = coord_name
                nonindex_coords.append((k, coord_dim))
                if coord_dim not in dims:
                    dims.append(coord_dim)
            else:
                # Stacked dimension
                index_coords.append(k)
                if k not in dims:
                    dims.append(k)

    # If multiple index coordinates, set a MultiIndex for them
    # Leave non-index coordinates out
    if len(dims) > 1:
        # Unstack MultiIndex, using a first-seen order
        xa = xa.set_index({dim: index_coords})  # type:ignore[dict-item]
        if unstack:
            xa = proper_unstack(xa, dim)
            # Now non-index coords will have become multi-dimensional
            # Drop extra dims if there is no ambiguity, otherwise raise error
            for coord, coord_dim in nonindex_coords:
                cvalue = xa.coords[coord]
                slice0 = cvalue.isel(
                    {
                        other_dim: 0
                        for other_dim in cvalue.dims
                        if other_dim != coord_dim
                    },
                    drop=True,
                )
                if (cvalue == slice0).all():
                    xa.coords[coord] = slice0
                else:
                    raise ValueError(
                        f"Non-index coord {coord} has different values for the same "
                        f"value of its dimension {coord_dim}"
                    )
        # Finally rename non-index coords
        xa = xa.rename(rename_map)

    elif len(nonindex_coords) == 1 and not index_coords:
        # Special case where the dim will be y (x)
        assert len(dims) == 1
        assert len(rename_map) == 1
        new_dim = nonindex_coords[0][1]
        old_dim, coord_name = next(iter(rename_map.items()))
        coord_value = xa.coords[xa.dims[0]]
        xa = xa.rename({old_dim: new_dim})
        del xa.coords[xa.dims[0]]
        xa.coords[coord_name] = (xa.dims[0], coord_value.data)

    else:
        assert len(dims) == 1
        # Rename dim_0, dim_1 as index coord (if necessary)
        xa = xa.rename({dim: dims[0]})
        # Finally rename non-index coords
        xa = xa.rename(rename_map)
    return xa
