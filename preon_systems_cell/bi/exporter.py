from __future__ import annotations


class BIExportRemovedError(RuntimeError):
    pass


def write_bi_bundle(*_args, **_kwargs) -> None:
    raise BIExportRemovedError("BI run exports were removed in the organism runtime reset.")


def write_export_zip(*_args, **_kwargs) -> None:
    raise BIExportRemovedError("BI run exports were removed in the organism runtime reset.")


def describe_export_formats() -> list[dict[str, str]]:
    return []


BI_EXPORT_FORMATS: tuple[str, ...] = ()
