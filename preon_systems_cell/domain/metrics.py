from __future__ import annotations

from preon_systems_cell.models import OrganismDetailResponse


def runtime_counts(detail: OrganismDetailResponse) -> dict[str, int]:
    return {
        "cells": len(detail.cells),
        "events": len(detail.events),
        "proteins": len(detail.proteins),
        "structure_requests": len(detail.structure_requests),
    }
