from __future__ import annotations


class ParquetStorageRemovedError(RuntimeError):
    pass


def write_parquet_run(*_args, **_kwargs) -> None:
    raise ParquetStorageRemovedError("Run Parquet storage was removed in the organism runtime reset.")
