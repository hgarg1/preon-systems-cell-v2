from __future__ import annotations

from typing import Any

from preon_systems_cell.models import OrganismDetailResponse


def build_runtime_tables(detail: OrganismDetailResponse) -> dict[str, list[dict[str, Any]]]:
    return {
        "organisms": [detail.organism.model_dump(mode="json")],
        "cells": [cell.model_dump(mode="json") for cell in detail.cells],
        "proteins": [protein.model_dump(mode="json") for protein in detail.proteins],
        "runtime_events": [event.model_dump(mode="json") for event in detail.events],
        "structure_requests": [request.model_dump(mode="json") for request in detail.structure_requests],
    }
