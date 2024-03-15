.. currentmodule:: ndcsv

What's New
==========

.. _whats-new.1.2.0:

v1.2.0 (2024-03-15)
-------------------
- Added support for Python 3.11 and 3.12
- Added support for xarray >=2022.6.0
- Added support for pandas >=1.5


.. _whats-new.1.1.0:

v1.1.0 (2022-03-26)
-------------------

- Bumped minimum version of dependencies:

  ========== ====== =====
  Dependency 1.0.0  1.1.0
  ========== ====== =====
  python     3.6    3.8
  numpy      1.13   1.14
  pandas     0.21   0.24
  xarray     0.10.9 0.14
  ========== ====== =====

- Added support for Python 3.8, 3.9, and 3.10
- Added support for recent versions of numpy, pandas, and xarray
- Added type annotations
- Lint with isort, black, mypy, pyupgrade. All linters are wrapped by pre-commit.
- Migrated CI to GitHub actions
- Developer documentation
- Fixed unit tests on Windows vs. pandas-0.24 `Jacob Lin`_
- Fixed noise when reading floats; e.g. "0.9988" was being read as
  0.9998799999999999 `Jacob Lin`_


.. _whats-new.1.0.0:

v1.0.0 (2019-01-02)
-------------------

- Open sourced and refactored from landg.idealcsv. Rewritten most of the code,
  unit tests, and documentation. Fixed many bugs. `Guido Imperiale`_


.. _`Guido Imperiale`: https://github.com/crusaderky
.. _`Jacob Lin`: https://github.com/jcclin