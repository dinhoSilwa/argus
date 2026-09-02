from __future__ import annotations

import re
from pathlib import Path

import mcp.types as types

from argus_mcp.config import load

TOOLS: list[types.Tool] = [
    types.Tool(
        name="read_project_context",
        description="Retorna contexto consolidado do projeto (stack, backlog em andamento, últimas decisões, instruções do agente).",
        inputSchema={"type": "object", "properties": {}},
    ),
    types.Tool(
        name="read_spec",
        description="Lê um arquivo de spec do vault por ID ou path.",
        inputSchema={
            "type": "object",
            "properties": {
                "id": {"type": "string", "description": "ID do item (ex: ARGUS-015)"},
                "path": {"type": "string", "description": "Path relativo ao vault"},
            },
        },
    ),
]


async def _read_project_context(args: dict[str, object]) -> str:
    try:
        cfg = load()
    except RuntimeError as e:
        return f"[ERRO] {e}"

    parts: list[str] = ["# Contexto do projeto"]

    parts.append(f"\n## Stack\n{cfg.stack}")

    backlog_file = cfg.vault_path / "03-specifications" / "backlog.md"
    if backlog_file.exists():
        in_progress = _extract_in_progress(backlog_file.read_text(encoding="utf-8"))
        parts.append(f"\n## Backlog (em andamento)\n{in_progress}")

    decision_file = cfg.vault_path / "00-project-charter" / "decision-log.md"
    if decision_file.exists():
        decisions = _extract_last_decisions(
            decision_file.read_text(encoding="utf-8"), n=5
        )
        parts.append(f"\n## Últimas decisões\n{decisions}")

    instrucao_file = cfg.vault_path / "11-ai-context" / "instrucao-ia.md"
    if instrucao_file.exists():
        parts.append(
            f"\n## Instruções do agente\n{instrucao_file.read_text(encoding='utf-8')}"
        )

    return "\n".join(parts)


async def _read_spec(args: dict[str, object]) -> str:
    spec_id = args.get("id")
    spec_path = args.get("path")

    if not spec_id and not spec_path:
        return "[ERRO] forneça id ou path"

    try:
        cfg = load()
    except RuntimeError as e:
        return f"[ERRO] {e}"

    if spec_path:
        target = cfg.vault_path / str(spec_path)
    else:
        target = _find_by_id(cfg.vault_path, str(spec_id))

    if target is None or not target.exists():
        return f"[ERRO] spec não encontrada: {spec_id or spec_path}"

    return target.read_text(encoding="utf-8")


def _extract_in_progress(backlog: str) -> str:
    match = re.search(r"## Em andamento\n(.*?)(?=\n---|\Z)", backlog, re.DOTALL)
    if not match:
        return "nenhum item em andamento"
    block = match.group(1).strip()
    rows = [
        row
        for row in block.splitlines()
        if row.startswith("|") and "---" not in row and "ID" not in row
    ]
    return "\n".join(rows) if rows else "nenhum item em andamento"


def _extract_last_decisions(log: str, n: int) -> str:
    entries = re.split(r"\n(?=## \[)", log)
    decision_entries = [e.strip() for e in entries if e.strip().startswith("## [")]
    last = decision_entries[-n:] if len(decision_entries) >= n else decision_entries
    return "\n\n".join(last)


def _find_by_id(vault: Path, spec_id: str) -> Path | None:
    for md in vault.rglob("*.md"):
        if spec_id.lower() in md.stem.lower():
            return md
        try:
            if (
                spec_id.lower()
                in md.read_text(encoding="utf-8", errors="ignore").lower()[:200]
            ):
                return md
        except OSError:
            continue
    return None


HANDLERS: dict[str, object] = {
    "read_project_context": _read_project_context,
    "read_spec": _read_spec,
}
