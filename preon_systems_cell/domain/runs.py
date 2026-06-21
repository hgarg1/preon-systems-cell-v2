from __future__ import annotations


class RunsRemovedError(RuntimeError):
    pass


def unsupported_runs_api() -> None:
    raise RunsRemovedError("Run records were removed in the organism runtime reset.")
