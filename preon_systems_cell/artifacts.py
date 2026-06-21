from __future__ import annotations


class RunArtifactsRemovedError(RuntimeError):
    pass


def write_run_artifacts(*_args, **_kwargs) -> None:
    raise RunArtifactsRemovedError("Run artifacts were removed in the organism runtime reset.")


def read_run_artifacts(*_args, **_kwargs) -> None:
    raise RunArtifactsRemovedError("Run artifacts were removed in the organism runtime reset.")
