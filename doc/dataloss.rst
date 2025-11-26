Data loss
=========
When writing xarray data, the following information is irreversibly lost:

- Name of the parent dimension of a MultiIndex (only the MultiIndex levels are
  retained)
- Scalar coordinates (not associated with a dimension)
- Array name
- Attributes
- Data types, unless they can be automatically inferred by :func:`pandas.read_csv`.
  or :func:`pandas.to_datetime`. Booleans receive special treatment.
- `Dask <https://dask.org>`_ chunks
