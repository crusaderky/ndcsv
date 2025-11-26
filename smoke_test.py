"""Test import the library and print essential information"""

import platform
import sys

import ndcsv

print("Python interpreter:", sys.executable)
print("Python version    :", sys.version)
print("Platform          :", platform.platform())
print("Library path      :", ndcsv.__file__)
print("Library version   :", ndcsv.__version__)
