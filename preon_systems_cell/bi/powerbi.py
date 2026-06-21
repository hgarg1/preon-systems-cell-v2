from __future__ import annotations


class PowerBIExportRemovedError(RuntimeError):
    pass


def write_powerbi_project(*_args, **_kwargs) -> None:
    raise PowerBIExportRemovedError("Power BI exports were removed in the organism runtime reset.")
