from __future__ import annotations


class ScenarioRemovedError(RuntimeError):
    pass


def load_scenario(*_args, **_kwargs) -> None:
    raise ScenarioRemovedError("Scenario YAML was removed in the organism runtime reset.")


def validate_scenario(*_args, **_kwargs) -> None:
    raise ScenarioRemovedError("Scenario validation was replaced by genome and signal validation.")
