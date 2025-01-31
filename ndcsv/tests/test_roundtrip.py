"""Test general use case:

1. Call write_csv() on an xarray.DataArray object,
2. Verify that the output text buffer matches the format specs
3. Call read_csv()
4. Verify that the output xarray.DataArray matches the original array
"""

import io

import numpy as np
import pandas as pd
import pytest
import xarray
from numpy import nan

from ndcsv import read_csv, write_csv


@pytest.mark.parametrize(
    "data,txt",
    [
        (5, "5\n"),
        (5.2, "5.2\n"),
        (1.0000000001, "1.0000000001\n"),
        (0, "0\n"),
        (0.0, "0.0\n"),
        (nan, "nan\n"),
        (True, "True\n"),
        (False, "False\n"),
        ("foo", "foo\n"),
    ],
)
def test_0d(data, txt):
    a = xarray.DataArray(data)
    buf = io.StringIO()
    write_csv(a, buf)
    assert buf.getvalue().replace("\r", "") == txt
    buf.seek(0)
    b = read_csv(buf)
    xarray.testing.assert_equal(a, b)


@pytest.mark.parametrize(
    "data,txt",
    [
        ([1, 2], "x,\nx1,1\nx2,2\n"),
        ([0.0, nan], "x,\nx1,0.0\nx2,\n"),
        ([nan, 0.0], "x,\nx1,nan\nx2,0.0\n"),
        ([nan, nan], "x,\nx1,nan\nx2,nan\n"),
        ([True, False], "x,\nx1,True\nx2,False\n"),
        (["foo", "bar"], "x,\nx1,foo\nx2,bar\n"),
    ],
)
def test_1d(data, txt):
    a = xarray.DataArray(data, dims=["x"], coords={"x": ["x1", "x2"]})
    buf = io.StringIO()
    write_csv(a, buf)
    assert buf.getvalue().replace("\r", "") == txt
    buf.seek(0)
    b = read_csv(buf)
    xarray.testing.assert_equal(a, b)


def test_1d_multiindex():
    a = xarray.DataArray(
        [[1, 2], [3, 4]], dims=["r", "c"], coords={"r": [10, 20], "c": [30, 40]}
    )
    b = a.stack(dim_0=["r", "c"])
    txt = "r,c,\n10,30,1\n10,40,2\n20,30,3\n20,40,4\n"

    buf = io.StringIO()
    write_csv(b, buf)
    assert buf.getvalue().replace("\r", "") == txt
    buf.seek(0)
    c = read_csv(buf)
    xarray.testing.assert_equal(c, a)
    buf.seek(0)
    c = read_csv(buf, unstack=False)
    xarray.testing.assert_equal(c, b)


@pytest.mark.parametrize(
    "data,txt",
    [
        ([[1, 2], [3, 4]], "c,c1,c2\nr,,\nr1,1,2\nr2,3,4\n"),
        ([[nan, 2], [3, 4]], "c,c1,c2\nr,,\nr1,,2.0\nr2,3.0,4.0\n"),
        ([[1, nan], [3, 4]], "c,c1,c2\nr,,\nr1,1.0,\nr2,3.0,4.0\n"),
        ([[nan, nan], [3, 4]], "c,c1,c2\nr,,\nr1,,\nr2,3.0,4.0\n"),
        ([[1, 2], [nan, nan]], "c,c1,c2\nr,,\nr1,1.0,2.0\nr2,,\n"),
        ([[nan, nan], [nan, nan]], "c,c1,c2\nr,,\nr1,,\nr2,,\n"),
        ([["x", "y"], ["w", "z"]], "c,c1,c2\nr,,\nr1,x,y\nr2,w,z\n"),
        (
            [[True, False], [False, True]],
            "c,c1,c2\nr,,\nr1,True,False\nr2,False,True\n",
        ),
    ],
)
def test_2d(data, txt):
    a = xarray.DataArray(
        data, dims=["r", "c"], coords={"r": ["r1", "r2"], "c": ["c1", "c2"]}
    )
    buf = io.StringIO()
    write_csv(a, buf)
    assert buf.getvalue().replace("\r", "") == txt
    buf.seek(0)
    b = read_csv(buf)
    xarray.testing.assert_equal(a, b)


@pytest.mark.parametrize("explicit_stack", [False, True])
def test_2d_multiindex_cols(explicit_stack):
    a = xarray.DataArray(
        np.arange(2 * 3 * 4).reshape((2, 3, 4)),
        dims=["x", "y", "z"],
        coords={
            "x": ["x0", "x1"],
            "y": ["y2", "y0", "y1"],  # test order is not compromised
            "z": ["z0", "z2", "z1", "z3"],
        },
    )
    b = a.stack(dim_1=["y", "z"])

    txt = (
        "y,y2,y2,y2,y2,y0,y0,y0,y0,y1,y1,y1,y1\n"
        "z,z0,z2,z1,z3,z0,z2,z1,z3,z0,z2,z1,z3\n"
        "x,,,,,,,,,,,,\n"
        "x0,0,1,2,3,4,5,6,7,8,9,10,11\n"
        "x1,12,13,14,15,16,17,18,19,20,21,22,23\n"
    )

    buf = io.StringIO()

    # >2 dimensional arrays get their dimensions beyond the first automatically
    # stacked
    if explicit_stack:
        write_csv(b, buf)
    else:
        write_csv(a, buf)

    assert buf.getvalue().replace("\r", "") == txt
    buf.seek(0)
    c = read_csv(buf)
    xarray.testing.assert_equal(a, c)
    buf.seek(0)
    c = read_csv(buf, unstack=False)
    xarray.testing.assert_equal(b, c)


def test_2d_multiindex_rows():
    a = xarray.DataArray(
        np.arange(2 * 3 * 4).reshape((2, 3, 4)),
        dims=["x", "y", "z"],
        coords={
            "x": ["x0", "x1"],
            "y": ["y2", "y0", "y1"],  # test order is not compromised
            "z": ["z0", "z2", "z1", "z3"],
        },
    )
    b = a.stack(dim_0=["y", "z"]).T

    txt = (
        "x,,x0,x1\n"
        "y,z,,\n"
        "y2,z0,0,12\n"
        "y2,z2,1,13\n"
        "y2,z1,2,14\n"
        "y2,z3,3,15\n"
        "y0,z0,4,16\n"
        "y0,z2,5,17\n"
        "y0,z1,6,18\n"
        "y0,z3,7,19\n"
        "y1,z0,8,20\n"
        "y1,z2,9,21\n"
        "y1,z1,10,22\n"
        "y1,z3,11,23\n"
    )

    buf = io.StringIO()
    write_csv(b, buf)
    assert buf.getvalue().replace("\r", "") == txt
    buf.seek(0)
    c = read_csv(buf)
    xarray.testing.assert_equal(a, c)
    buf.seek(0)
    c = read_csv(buf, unstack=False)
    xarray.testing.assert_equal(b, c)


@pytest.mark.parametrize("explicit_stack", [False, True])
def test_2d_multiindex_both(explicit_stack):
    a = xarray.DataArray(
        np.arange(16).reshape((2, 2, 2, 2)),
        dims=["x", "y", "z", "w"],
        coords={
            "x": ["x0", "x1"],
            "y": ["y0", "y1"],
            "z": ["z0", "z1"],
            "w": ["w0", "w1"],
        },
    )
    b = a.stack(dim_0=["x", "y"]).transpose("dim_0", "z", "w")
    c = b.stack(dim_1=["z", "w"])

    txt = (
        "z,,z0,z0,z1,z1\n"
        "w,,w0,w1,w0,w1\n"
        "x,y,,,,\n"
        "x0,y0,0,1,2,3\n"
        "x0,y1,4,5,6,7\n"
        "x1,y0,8,9,10,11\n"
        "x1,y1,12,13,14,15\n"
    )

    buf = io.StringIO()
    if explicit_stack:
        write_csv(c, buf)
    else:
        write_csv(b, buf)
    assert buf.getvalue().replace("\r", "") == txt
    buf.seek(0)
    d = read_csv(buf)
    xarray.testing.assert_equal(a, d)
    buf.seek(0)
    d = read_csv(buf, unstack=False)
    xarray.testing.assert_equal(c, d)


def test_xarray_nocoords():
    a = xarray.DataArray([[1, 2], [3, 4]], dims=["r", "c"])
    b = a.copy()
    b.coords["r"] = [0, 1]
    b.coords["c"] = [0, 1]
    txt = "c,0,1\nr,,\n0,1,2\n1,3,4\n"

    buf = io.StringIO()
    write_csv(a, buf)
    assert buf.getvalue().replace("\r", "") == txt
    buf.seek(0)
    c = read_csv(buf)
    xarray.testing.assert_equal(b, c)


def test_numerical_ids1():
    """An index full of numerical IDs padded on the left with zeros
    won't accidentally convert them to int as long as at least one element
    can't be cast to int
    """
    a = xarray.DataArray([1, 2, 3], dims=["x"], coords={"x": ["01", "02", "S1"]})
    buf = io.StringIO()
    write_csv(a, buf)
    buf.seek(0)
    b = read_csv(buf)
    xarray.testing.assert_equal(a, b)


def test_numerical_ids2():
    a = xarray.DataArray([1, 2], dims=["x"], coords={"x": ["01", "02"]})
    b = xarray.DataArray([1, 2], dims=["x"], coords={"x": [1, 2]})
    buf = io.StringIO()
    write_csv(a, buf)
    buf.seek(0)
    c = read_csv(buf)
    xarray.testing.assert_equal(b, c)


@pytest.mark.parametrize("unstack", [False, True])
def test_nonindex_coords(unstack):
    a = xarray.DataArray(
        [1, 2], dims=["x"], coords={"x": [10, 20], "y": ("x", [30, 40])}
    )
    txt = "x,y (x),\n10,30,1\n20,40,2\n"
    buf = io.StringIO()
    write_csv(a, buf)
    assert buf.getvalue().replace("\r", "") == txt
    buf.seek(0)
    b = read_csv(buf, unstack=unstack)
    xarray.testing.assert_equal(a, b)


def test_shape1():
    # Test the edge case of an array with shape (1, )
    a = xarray.DataArray([1], dims=["x"], coords={"x": ["x1"]})
    buf = io.StringIO()
    write_csv(a, buf)
    assert buf.getvalue().replace("\r", "") == "x,\nx1,1\n"
    buf.seek(0)
    b = read_csv(buf)
    xarray.testing.assert_equal(a, b)


def test_duplicate_index():
    """Duplicate indices are OK as long as you don't try unstacking"""
    a = xarray.DataArray([1, 2], dims=["x"], coords={"x": [10, 10]})
    txt = "x,\n10,1\n10,2\n"

    buf = io.StringIO()
    write_csv(a, buf)
    assert buf.getvalue().replace("\r", "") == txt
    buf.seek(0)
    b = read_csv(buf)
    xarray.testing.assert_equal(a, b)


def test_duplicate_index_multiindex():
    """Duplicate indices are OK as long as you don't try to unstack"""
    a = xarray.DataArray(
        [1, 2],
        dims=["dim_0"],
        coords={
            "dim_0": pd.MultiIndex.from_tuples([(10, 10), (10, 10)], names=["x", "y"])
        },
    )

    txt = "x,y,\n10,10,1\n10,10,2\n"

    buf = io.StringIO()
    write_csv(a, buf)
    assert buf.getvalue().replace("\r", "") == txt
    buf.seek(0)
    b = read_csv(buf, unstack=False)
    xarray.testing.assert_equal(a, b)
