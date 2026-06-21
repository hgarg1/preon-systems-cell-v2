from __future__ import annotations


class ParquetExportRemovedError(RuntimeError):
    pass


def write_parquet_tables(*_args, **_kwargs) -> None:
    raise ParquetExportRemovedError("Parquet BI exports were removed in the organism runtime reset.")
