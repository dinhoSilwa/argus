from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from argus_mcp.tools.memory import (
    _add_block_note,
    _extract_item_text,
    _move_to_complete,
    _move_to_in_progress,
)

BACKLOG = textwrap.dedent("""\
    ## Em andamento

    | ID | Item | Responsável |
    |----|------|-------------|

    ---

    ## Pendente

    | ID | Item | Dependência |
    |----|------|-------------|
    | ARGUS-020 | create_feature | ARGUS-014 |
    | ARGUS-021 | create_endpoint | ARGUS-014 |

    ---

    ## Concluído

    | ID | Item | Data |
    |----|------|------|
""")


def test_move_to_in_progress():
    result = _move_to_in_progress(BACKLOG, "ARGUS-020")
    assert "ARGUS-020" in result.split("## Em andamento")[1].split("---")[0]
    assert result.count("ARGUS-020") == 1


def test_move_to_complete():
    result = _move_to_complete(BACKLOG, "ARGUS-020")
    assert "~~ARGUS-020~~" in result
    assert result.count("ARGUS-020") == 1


def test_add_block_note():
    result = _add_block_note(BACKLOG, "ARGUS-021", "aguardando dependência")
    assert "⚠️ aguardando dependência" in result


def test_item_not_found_returns_unchanged():
    result = _move_to_in_progress(BACKLOG, "ARGUS-999")
    assert result == BACKLOG


def test_extract_item_text():
    row = "| ARGUS-020 | create_feature | ARGUS-014 |"
    assert _extract_item_text(row) == "create_feature"


@pytest.mark.asyncio
async def test_save_decision_no_root(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("ARGUS_PROJECT_ROOT", raising=False)
    monkeypatch.chdir("/")
    from argus_mcp.tools.memory import _save_decision
    result = await _save_decision({"title": "t", "context": "c", "decision": "d", "reason": "r"})
    assert result.startswith("[ERRO]")


@pytest.mark.asyncio
async def test_save_decision_writes_entry(tmp_path: Path):
    vault = tmp_path / "vault"
    charter = vault / "00-project-charter"
    charter.mkdir(parents=True)
    log = charter / "decision-log.md"
    log.write_text("# Decision Log\n\n---\n")

    import os
    os.environ["ARGUS_PROJECT_ROOT"] = str(tmp_path)
    os.environ["ARGUS_VAULT_PATH"] = str(vault)

    from argus_mcp.tools.memory import _save_decision
    result = await _save_decision({
        "title": "Teste",
        "context": "contexto",
        "decision": "decisão",
        "reason": "motivo",
    })

    del os.environ["ARGUS_PROJECT_ROOT"]
    del os.environ["ARGUS_VAULT_PATH"]

    assert result == "Decisão salva: Teste"
    content = log.read_text()
    assert "## [" in content
    assert "Teste" in content
    assert "**Contexto:** contexto" in content
