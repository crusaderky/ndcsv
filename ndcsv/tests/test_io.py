import bz2
import gzip
import io
import lzma

import pytest
import xarray

from ndcsv import read_csv, write_csv


def test_str_output():
    a = xarray.DataArray(1)
    assert write_csv(a) == "1\n"


def test_buf_io():
    a = xarray.DataArray(1)
    buf = io.StringIO()
    write_csv(a, buf)
    assert buf.getvalue() == "1\n"
    buf.seek(0)
    b = read_csv(buf)
    xarray.testing.assert_equal(a, b)


@pytest.mark.parametrize(
    "open_func,ext",
    [
        (open, "csv"),
        (gzip.open, "csv.gz"),
        (bz2.open, "csv.bz2"),
        (lzma.open, "csv.xz"),
    ],
)
def test_file_io(tmpdir, open_func, ext):
    a = xarray.DataArray(1)
    fname = f"{tmpdir}/test.{ext}"
    write_csv(a, fname)
    with open_func(fname, "rt") as fh:
        assert fh.read() == "1\n"
    b = read_csv(fname)
    xarray.testing.assert_equal(a, b)
