from __future__ import annotations

import re
from datetime import date
from typing import Any

import mcp.types as types

from argus_mcp.config import load

TOOLS: list[types.Tool] = [
    types.Tool(
        name="save_decision",
        description="Acrescenta uma entrada formatada no decision-log.md do vault.",
        input_schema={
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "context": {"type": "string"},
                "decision": {"type": "string"},
                "reason": {"type": "string"},
                "discarded": {"type": "string"},
            },
            "required": ["title", "context", "decision", "reason"],
        },
    ),
    types.Tool(
        name="update_backlog",
        description="Move um item do backlog (start | complete | block).",
        input_schema={
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "action": {"type": "string", "enum": ["start", "complete", "block"]},
                "note": {"type": "string"},
            },
            "required": ["id", "action"],
        },
    ),
]


async def _save_decision(args: dict[str, object]) -> str:
    try:
        cfg = load()
    except RuntimeError as e:
        return f"[ERRO] {e}"

    decision_file = cfg.vault_path / "00-project-charter" / "decision-log.md"
    if not decision_file.exists():
        return f"[ERRO] decision-log.md não encontrado em {decision_file}"

    today = date.today().isoformat()
    title = args.get("title", "")
    entry_lines = [
        f"\n## [{today}] {title}",
        f"\n**Contexto:** {args.get('context', '')}",
        f"**Decisão:** {args.get('decision', '')}",
        f"**Motivo:** {args.get('reason', '')}",
    ]
    if discarded := args.get("discarded"):
        entry_lines.append(f"**Alternativas descartadas:** {discarded}")

    entry = "\n".join(entry_lines)
    current = decision_file.read_text(encoding="utf-8")
    decision_file.write_text(current.rstrip() + "\n" + entry + "\n", encoding="utf-8")

    return f"Decisão salva: {title}"


async def _update_backlog(args: dict[str, object]) -> str:
    try:
        cfg = load()
    except RuntimeError as e:
        return f"[ERRO] {e}"

    backlog_file = cfg.vault_path / "03-specifications" / "backlog.md"
    if not backlog_file.exists():
        return f"[ERRO] backlog.md não encontrado em {backlog_file}"

    item_id = str(args.get("id", ""))
    action = str(args.get("action", ""))
    note = str(args.get("note", ""))

    if action not in ("start", "complete", "block"):
        return f"[ERRO] action inválida: {action}"

    content = backlog_file.read_text(encoding="utf-8")

    if action == "start":
        content = _move_to_in_progress(content, item_id)
    elif action == "complete":
        content = _move_to_complete(content, item_id)
    elif action == "block":
        content = _add_block_note(content, item_id, note)

    if content is None:
        return f"[ERRO] item não encontrado: {item_id}"

    backlog_file.write_text(content, encoding="utf-8")
    return f"Backlog atualizado: {item_id} → {action}"


def _find_item_row(content: str, item_id: str) -> re.Match[str] | None:
    pattern = rf"(\| {re.escape(item_id)} \|[^\n]+)"
    return re.search(pattern, content)


def _move_to_in_progress(content: str, item_id: str) -> str:
    match = _find_item_row(content, item_id)
    if not match:
        return content

    row = match.group(1)
    content = content.replace(row, "", 1)

    in_progress_header = (
        "## Em andamento\n\n| ID | Item | Responsável |\n|----|------|-------------|"
    )
    insert_row = f"| {item_id} | {_extract_item_text(row)} | — |"
    return content.replace(
        in_progress_header,
        f"{in_progress_header}\n{insert_row}",
        1,
    )


def _move_to_complete(content: str, item_id: str) -> str:
    match = _find_item_row(content, item_id)
    if not match:
        return content

    row = match.group(1)
    item_text = _extract_item_text(row)
    today = date.today().isoformat()
    content = content.replace(row, "", 1)

    complete_row = f"| ~~{item_id}~~ | ~~{item_text}~~ | {today} |"
    concluido_marker = "## Concluído\n\n| ID | Item | Data |\n|----|------|------|"
    return content.replace(
        concluido_marker,
        f"{concluido_marker}\n{complete_row}",
        1,
    )


def _add_block_note(content: str, item_id: str, note: str) -> str:
    match = _find_item_row(content, item_id)
    if not match:
        return content

    row = match.group(1)
    suffix = f" ⚠️ {note}" if note else " ⚠️ bloqueado"
    return content.replace(row, row.rstrip() + suffix, 1)


def _extract_item_text(row: str) -> str:
    parts = [p.strip() for p in row.split("|") if p.strip()]
    return parts[1] if len(parts) > 1 else row


HANDLERS: dict[str, Any] = {
    "save_decision": _save_decision,
    "update_backlog": _update_backlog,
}
