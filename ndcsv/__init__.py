import pkg_resources

from .read import read_csv
from .write import write_csv

try:
    __version__ = pkg_resources.get_distribution("ndcsv").version
except Exception:  # pragma: nocover
    # Local copy, not installed with setuptools
    __version__ = "999"

__all__ = ("__version__", "read_csv", "write_csv")
