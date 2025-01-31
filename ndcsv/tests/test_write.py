"""Test edge cases that only require write_csv()
Normal use cases are tested in :mod:`test_roundtrip`
"""

import io

import pytest
import xarray
from numpy import nan

from ndcsv import write_csv


@pytest.mark.parametrize(
    "nancoord",
    [
        # coord dtype = float
        [nan, 1],
        [1, nan],
        [nan, nan],
        # coord dtype = str
        ["", "c1"],
        ["c0", ""],
        ["", ""],
        # coord dtype = object
        [1, ""],
        ["", 1],
    ],
)
def test_blank_coord(nancoord):
    """Empty strings and NaNs in the coords must trigger a ValueError as
    there is no way to round-trip them back
    """
    # Simple index
    i0 = xarray.DataArray([10, 20], dims=["x"], coords={"x": nancoord}, name="i0")
    # MultiIndex on the columns; 1st level
    i1 = xarray.DataArray(
        [[10, 20], [30, 40]], dims=["x", "y"], coords={"x": nancoord}, name="i1"
    ).stack(s=["x", "y"])
    # MultiIndex on the rows; 1st level
    i2 = (
        xarray.DataArray(
            [[10, 20], [30, 40]], dims=["x", "y"], coords={"x": nancoord}, name="i2"
        )
        .stack(s=["x", "y"])
        .T
    )
    # MultiIndex on the columns; 2nd level
    i3 = xarray.DataArray(
        [[10, 20], [30, 40]], dims=["x", "y"], coords={"y": nancoord}, name="i3"
    ).stack(s=["x", "y"])
    # MultiIndex on the rows; 2nd level
    i4 = (
        xarray.DataArray(
            [[10, 20], [30, 40]], dims=["x", "y"], coords={"y": nancoord}, name="i4"
        )
        .stack(s=["x", "y"])
        .T
    )

    if "" in nancoord:
        msg = "Empty string in index"
    else:
        msg = "NaN in index"

    for inp in (i0, i1, i2, i3, i4):
        print(inp)
        buf = io.StringIO()
        with pytest.raises(ValueError, match=msg):
            write_csv(inp, buf)
