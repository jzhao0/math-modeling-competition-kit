"""Competition project scaffolding."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from mmkit.benchmark import init_benchmark
from mmkit.coordination import init_coordination

from .project import WORKSPACE_DIRS, init_project as _init_project


def init_project(
    destination: str | Path,
    *,
    competition: str,
    year: int | str,
    project_name: str | None = None,
    force: bool = False,
) -> dict[str, Any]:
    """Create a project scaffold plus coordination and benchmark control files."""

    report = _init_project(
        destination,
        competition=competition,
        year=year,
        project_name=project_name,
        force=force,
    )
    report["coordination"] = init_coordination(destination)
    report["benchmark"] = init_benchmark(destination)
    return report


__all__ = ["WORKSPACE_DIRS", "init_project"]
