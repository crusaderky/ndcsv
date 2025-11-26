"""Test edge cases that only require read_csv()
Normal use cases are tested in :mod:`test_roundtrip`
"""

import io

import numpy as np
import pandas as pd
import pytest
import xarray

from ndcsv import read_csv


def test_malformed_input():
    buf = io.StringIO("foo,bar,baz")
    with pytest.raises(ValueError, match="Malformed N-dimensional CSV"):
        read_csv(buf)


@pytest.mark.parametrize("unstack", [True, False])
def test_coords_dtypes(unstack):
    buf = io.StringIO(
        "x1,,1,2,3\n"
        "x2,,10/11/2017,01/02/2018,12/12/2018\n"
        "x3,,true,false,true\n"
        "y1,y2,,,\n"
        "1.5,s2,10,20,30\n"
        "1.7,003,10,20,30"
    )
    a = read_csv(buf, unstack=unstack)
    if not unstack:
        # Manually unstack
        a = a.unstack("dim_1")

    assert a.x1.dtype.kind == "i"  # int
    assert a.x2.dtype.kind == "M"  # numpy.datetime64
    assert a.y1.dtype.kind == "f"  # float
    assert a.x3.dtype.kind == "b"  # bool
    assert a.y2.dtype.kind == "U"  # unicode string


def test_coords_bool():
    buf = io.StringIO(
        "y,true,false,TRUE,FALSE,True,False,Y,N,y,n,YES,NO,"
        "Yes,No,yes,no,T,F,T,F\n"
        "x\n"
        "x0" + ",1" * 20 + "\n"
    )
    a = read_csv(buf)
    assert a.y.values.tolist() == [True, False] * 10


@pytest.mark.parametrize(
    "s",
    [
        "2017-11-13,2017-11-14",
        "13/11/2017,14/11/2017",
        "11/13/2017,11/14/2017",
        "13 Nov 2017,14 Nov 2017",
    ],
)
def test_coords_date(s):
    buf = io.StringIO(f"y,{s}\nx,,\nx0,1,2\n")
    a = read_csv(buf)
    np.testing.assert_equal(
        pd.to_datetime(["13 Nov 2017", "14 Nov 2017"]).values, a.coords["y"].values
    )


def test_2d_onecol_nomultiindex():
    """2D array with shape (n, 1) and no multiindex"""
    buf = io.StringIO(
        "riskfactor,foo\n"
        "percentile,\n"
        "0.0,0.0\n"
        "0.11,11.11\n"
        "0.22,22.22\n"
        "0.33,33.33\n"
        "1.0,100.0"
    )
    a = read_csv(buf)
    b = xarray.DataArray(
        [[0.0], [11.11], [22.22], [33.33], [100.0]],
        dims=["percentile", "riskfactor"],
        coords={"percentile": [0.0, 0.11, 0.22, 0.33, 1.0], "riskfactor": ["foo"]},
    )
    xarray.testing.assert_equal(a, b)


def test_2d_onecol_multiindex():
    """2D array with shape (n, 1) and multiindex"""
    csv_buf = io.StringIO(
        "riskfactor,,foo\n"
        "id,percentile,\n"
        "S001,0.0,0.0\n"
        "S001,0.11,11.11\n"
        "S001,0.22,22.22\n"
        "S001,0.33,33.33\n"
        "S001,1.0,100.0"
    )
    a = read_csv(csv_buf)
    b = xarray.DataArray(
        [[[0.0, 11.11, 22.22, 33.33, 100.0]]],
        dims=["riskfactor", "id", "percentile"],
        coords={
            "riskfactor": ["foo"],
            "id": ["S001"],
            "percentile": [0.0, 0.11, 0.22, 0.33, 1.0],
        },
    )
    xarray.testing.assert_equal(a, b)


def test_ambiguous_nonindex_coords():
    """Test when non-index coords have multiple values for the matching
    index coord
    """
    buf = io.StringIO("x,y,z (x),\n0,0,0,1\n0,1,1,1\n")
    with pytest.raises(
        ValueError,
        match=r"Non-index coord z \(x\) has different values for "
        r"the same value of its dimension x",
    ):
        read_csv(buf)


@pytest.mark.parametrize("unstack", [False, True])
def test_nonindex_coords_with_multiindex(unstack):
    buf = io.StringIO("x,y,z (x),\nx1,y1,z1,1\nx1,y2,z1,2\nx2,y1,z2,3\nx2,y2,z2,4\n")
    a = read_csv(buf, unstack=unstack)
    if unstack:
        b = xarray.DataArray(
            [[1, 2], [3, 4]],
            dims=["x", "y"],
            coords={
                "x": ["x1", "x2"],
                "y": ["y1", "y2"],
                "z": ("x", ["z1", "z2"]),
            },
        )
    else:
        b = xarray.DataArray(
            [1, 2, 3, 4],
            dims=["dim_0"],
            coords={
                "dim_0": pd.MultiIndex.from_tuples(
                    [("x1", "y1"), ("x1", "y2"), ("x2", "y1"), ("x2", "y2")],
                    names=["x", "y"],
                ),
                "z": ("dim_0", ["z1", "z1", "z2", "z2"]),
            },
        )

    xarray.testing.assert_equal(a, b)


@pytest.mark.parametrize("unstack", [False, True])
def test_missing_index_coord1(unstack):
    """The index coord may be missing as long as matching non-index coord(s)
    spell out the dim name
    """
    buf = io.StringIO("y (x),\n10,1\n20,2\n")
    b = xarray.DataArray([1, 2], dims=["x"], coords={"y": ("x", [10, 20])})
    a = read_csv(buf, unstack=unstack)
    xarray.testing.assert_equal(a, b)


@pytest.mark.parametrize("unstack", [False, True])
def test_missing_index_coord2(unstack):
    """Same as above, but with 2 non-index coords which will instigate
    pandas to create a MultiIndex
    """
    buf = io.StringIO("y (x),z (x),\n10,30,1\n20,40,2\n")
    b = xarray.DataArray(
        [1, 2], dims=["x"], coords={"y": ("x", [10, 20]), "z": ("x", [30, 40])}
    )
    a = read_csv(buf, unstack=unstack)
    xarray.testing.assert_equal(a, b)


@pytest.mark.parametrize(
    "txt",
    [
        "0.99988\n",
        "x,\nx1,0.99988\n",
        "c,c1\nr,\nr1,0.99988\n",
    ],
)
def test_float_precision(txt):
    """Test that when ndcsv.read_csv() calls pd.read_csv(), the argument
    float_precision='high' is used.  This is to combat the below behaviour::

        >>> pd.read_csv(io.StringIO('x\n0.99988\n'),
        ...                 squeeze=True)[0]
        0.9998799999999999
        >>> pd.read_csv(io.StringIO('x\n0.99988\n'),
        ...                 squeeze=True,
        ...                 float_precision='high')[0]
        0.99988

    The ndcsv.read_csv() calls pd.read_csv() in three different ways,
    depending on the number of header rows -- no header row, one header
    row, and more than one header rows.  The precision tests in this module
    are organised in the same manner.
    """
    buf = io.StringIO(txt)
    assert read_csv(buf).values.ravel()[0] == 0.99988
