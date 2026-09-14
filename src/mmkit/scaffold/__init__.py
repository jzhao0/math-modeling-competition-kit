"""Competition project scaffolding."""

from __future__ import annotations

from pathlib import Path
from typing import Any

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
    """Create a project scaffold and ensure machine-readable coordination state exists."""

    report = _init_project(
        destination,
        competition=competition,
        year=year,
        project_name=project_name,
        force=force,
    )
    report["coordination"] = init_coordination(destination)
    return report


__all__ = ["WORKSPACE_DIRS", "init_project"]
