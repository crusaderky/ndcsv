.. currentmodule:: ndcsv

What's New
==========

.. _whats-new.1.1.0:

v1.1.0 (Unreleased)
-------------------

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