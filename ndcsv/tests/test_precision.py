"""Test general use case:
Test precision edge case and provide context manger
`patch_pandas_read_csv_assert_float_precision_high`
"""
import contextlib
import io
import sys

import xarray

from ndcsv import write_csv, read_csv


@contextlib.contextmanager
def patch_pandas_read_csv_assert_float_precision_high(func):
    """Context manager that on-the-fly patch in `pandas.read_csv` with a
    substitute which check if the arguments contain float_precision='high'
    before invoking the original `pandas.read_csv`.  Restore the original
    `pandas.read_csv` on exit context management block.

    Usage, instead of:

        some_code
        return_value = ndcsv.read_csv(...)
        some_more_code

    Do this:

        some_code
        with patch_pandas_read_csv_assert_float_precision_high(ndcsv.read_csv):
            return_value = ndcsv.read_csv(...)
        some_more_code

    Note: that this context manager function could have been written as a
    decorator to the test case functions.  However, as some test cases are
    decorated with `pytest.mark.parametrize`, which insist certain positional
    arguments to be named by certain names.  It is therefore difficult to
    generalise the argument passing, so here we resort to a context manager
    that is just to wrap around ``
    """
    original_pandas_read_csv = sys.modules['pandas'].read_csv

    def substitute_pandas_read_csv(*args, **kwargs):

        assert 'float_precision' in kwargs
        assert kwargs['float_precision'] == 'high'
        return original_pandas_read_csv(*args, **kwargs)

    try:
        sys.modules['pandas'].read_csv = substitute_pandas_read_csv
        yield func
    finally:
        sys.modules['pandas'].read_csv = original_pandas_read_csv


def test_precision():
    a = xarray.DataArray(0.99988)

    buf = io.StringIO()
    write_csv(a, buf)
    assert buf.getvalue() == '0.99988\n'
    buf.seek(0)
    b = read_csv(buf)
    xarray.testing.assert_equal(a, b)
