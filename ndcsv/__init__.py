import importlib.metadata

from .read import read_csv
from .write import write_csv

try:
    __version__ = importlib.metadata.version("ndcsv")
except importlib.metadata.PackageNotFoundError:  # pragma: nocover
    # Local copy, not installed with pip
    __version__ = "999"

__all__ = ("__version__", "read_csv", "write_csv")
