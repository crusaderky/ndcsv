import io

import pandas as pd

from ndcsv import write_csv


def test_write_dataframe():
    a = pd.DataFrame([[1, 2, 3], [4, 5, 6]])
    txt = "dim_1,0,1,2\ndim_0,,,\n0,1,2,3\n1,4,5,6\n"
    buf = io.StringIO()
    write_csv(a, buf)
    print(buf.getvalue())
    assert buf.getvalue().replace("\r", "") == txt

    # add index/columns labels
    a.index = ["i1", "i2"]
    a.columns = ["c1", "c2", "c3"]
    txt = "dim_1,c1,c2,c3\ndim_0,,,\ni1,1,2,3\ni2,4,5,6\n"
    buf = io.StringIO()
    write_csv(a, buf)
    assert buf.getvalue().replace("\r", "") == txt

    # add index/columns names
    a.index.name = "r"
    a.columns.name = "c"
    txt = "c,c1,c2,c3\nr,,,\ni1,1,2,3\ni2,4,5,6\n"
    buf = io.StringIO()
    write_csv(a, buf)
    print(buf.getvalue())
    assert buf.getvalue().replace("\r", "") == txt


def test_write_series():
    a = pd.Series([10, 20])
    txt = "dim_0,\n0,10\n1,20\n"
    buf = io.StringIO()
    write_csv(a, buf)
    print(buf.getvalue())
    assert buf.getvalue().replace("\r", "") == txt

    # add index labels
    a.index = ["i1", "i2"]
    txt = "dim_0,\ni1,10\ni2,20\n"
    buf = io.StringIO()
    write_csv(a, buf)
    print(buf.getvalue())
    assert buf.getvalue().replace("\r", "") == txt

    # add index/columns names
    a.index.name = "r"
    txt = "r,\ni1,10\ni2,20\n"
    buf = io.StringIO()
    write_csv(a, buf)
    print(buf.getvalue())
    assert buf.getvalue().replace("\r", "") == txt
