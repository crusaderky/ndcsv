"""Test that when ndcsv.read_csv() calls pandas.read_csv(), the argument
float_precision='high' is used.  This is to combat the below behaviour.

    >>> pandas.read_csv(io.StringIO('x\n0.99988\n'),
    ...                 squeeze=True)[0]
    0.9998799999999999
    >>> pandas.read_csv(io.StringIO('x\n0.99988\n'),
    ...                 squeeze=True,
    ...                 float_precision='high')[0]
    0.99988

The ndcsv.read_csv() calls pandas.read_csv() in three different ways,
depending on the number of header rows -- no header row, one header
row, and more than one header rows.  The precision tests in this module
are organised in the same manner.
"""
import io

import pytest
import xarray

from ndcsv import write_csv, read_csv


@pytest.mark.parametrize('data,txt', [
    (0.99988, '0.99988\n'),
])
def test_read_csv_precision_no_header_row(data, txt):
    a = xarray.DataArray(data)
    buf = io.StringIO()
    write_csv(a, buf)
    assert buf.getvalue().replace('\r', '') == txt
    buf.seek(0)
    b = read_csv(buf)
    xarray.testing.assert_equal(a, b)


@pytest.mark.parametrize('data,txt', [
    ([0.99988, 0.99988], 'x,\n'
                         'x1,0.99988\n'
                         'x2,0.99988\n'),
])
def test_read_csv_precision_one_header_row(data, txt):
    a = xarray.DataArray(data, dims=['x'], coords={'x': ['x1', 'x2']})
    buf = io.StringIO()
    write_csv(a, buf)
    assert buf.getvalue().replace('\r', '') == txt
    buf.seek(0)
    b = read_csv(buf)
    xarray.testing.assert_equal(a, b)


@pytest.mark.parametrize('data,txt', [
    ([[0.99988, 0.99988], [0.99988, 0.99988]], 'c,c1,c2\n'
                                               'r,,\n'
                                               'r1,0.99988,0.99988\n'
                                               'r2,0.99988,0.99988\n'),
])
def test_read_csv_precision_more_than_one_header_rows(data, txt):
    a = xarray.DataArray(data, dims=['r', 'c'],
                         coords={'r': ['r1', 'r2'], 'c': ['c1', 'c2']})
    buf = io.StringIO()
    write_csv(a, buf)
    assert buf.getvalue().replace('\r', '') == txt
    buf.seek(0)
    b = read_csv(buf)
    xarray.testing.assert_equal(a, b)
