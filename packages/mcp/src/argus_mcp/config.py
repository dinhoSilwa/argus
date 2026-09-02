from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Config:
    project_root: Path
    vault_path: Path
    stack: str


def load() -> Config:
    if root := os.getenv("ARGUS_PROJECT_ROOT"):
        project_root = Path(root)
    else:
        project_root = _find_project_root()

    if vault := os.getenv("ARGUS_VAULT_PATH"):
        vault_path = Path(vault)
    else:
        vault_path = project_root / "vault"

    return Config(
        project_root=project_root,
        vault_path=vault_path,
        stack=_read_stack(project_root),
    )


def _find_project_root() -> Path:
    for directory in [Path.cwd(), *Path.cwd().parents]:
        if (directory / ".argus").exists() or (directory / "CLAUDE.md").exists():
            return directory
    raise RuntimeError("project root não encontrado — rode argus init primeiro")


def _read_stack(root: Path) -> str:
    config_file = root / ".argus" / "config.json"
    if config_file.exists():
        data = json.loads(config_file.read_text(encoding="utf-8"))
        return str(data.get("stack", "unknown"))
    return "unknown"
