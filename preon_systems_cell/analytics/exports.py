from __future__ import annotations


class AnalyticsExportRemovedError(RuntimeError):
    pass


def export_run_analytics(*_args, **_kwargs) -> None:
    raise AnalyticsExportRemovedError("Run analytics exports were removed in the organism runtime reset.")
