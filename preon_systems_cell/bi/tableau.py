from __future__ import annotations


class TableauExportRemovedError(RuntimeError):
    pass


def write_tableau_hyper(*_args, **_kwargs) -> None:
    raise TableauExportRemovedError("Tableau exports were removed in the organism runtime reset.")
