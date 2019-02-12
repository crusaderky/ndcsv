import io
import pandas
from ndcsv import write_csv


def test_write_dataframe():
    a = pandas.DataFrame([[1, 2, 3], [4, 5, 6]])
    txt = ("dim_1,0,1,2\n"
           "dim_0,,,\n"
           "0,1,2,3\n"
           "1,4,5,6\n")
    buf = io.StringIO()
    write_csv(a, buf)
    print(buf.getvalue())
    assert buf.getvalue().replace('\r', '') == txt

    # add index/columns labels
    a.index = ['i1', 'i2']
    a.columns = ['c1', 'c2', 'c3']
    txt = ("dim_1,c1,c2,c3\n"
           "dim_0,,,\n"
           "i1,1,2,3\n"
           "i2,4,5,6\n")
    buf = io.StringIO()
    write_csv(a, buf)
    assert buf.getvalue().replace('\r', '') == txt

    # add index/columns names
    a.index.name = 'r'
    a.columns.name = 'c'
    txt = ("c,c1,c2,c3\n"
           "r,,,\n"
           "i1,1,2,3\n"
           "i2,4,5,6\n")
    buf = io.StringIO()
    write_csv(a, buf)
    print(buf.getvalue())
    assert buf.getvalue().replace('\r', '') == txt


def test_write_series():
    a = pandas.Series([10, 20])
    txt = ("dim_0,\n"
           "0,10\n"
           "1,20\n")
    buf = io.StringIO()
    write_csv(a, buf)
    print(buf.getvalue())
    assert buf.getvalue().replace('\r', '') == txt

    # add index labels
    a.index = ['i1', 'i2']
    txt = ("dim_0,\n"
           "i1,10\n"
           "i2,20\n")
    buf = io.StringIO()
    write_csv(a, buf)
    print(buf.getvalue())
    assert buf.getvalue().replace('\r', '') == txt

    # add index/columns names
    a.index.name = 'r'
    txt = ("r,\n"
           "i1,10\n"
           "i2,20\n")
    buf = io.StringIO()
    write_csv(a, buf)
    print(buf.getvalue())
    assert buf.getvalue().replace('\r', '') == txt
