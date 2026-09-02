from __future__ import annotations

import pytest

from argus_mcp.tools.context import _extract_in_progress, _extract_last_decisions


def test_extract_in_progress_with_items():
    backlog = """## Em andamento

| ID | Item | Responsável |
|----|------|-------------|
| ARGUS-001 | Especificação do produto | — |

---
"""
    result = _extract_in_progress(backlog)
    assert "ARGUS-001" in result


def test_extract_in_progress_empty():
    backlog = """## Em andamento

| ID | Item | Responsável |
|----|------|-------------|

---
"""
    result = _extract_in_progress(backlog)
    assert result == "nenhum item em andamento"


def test_extract_last_decisions_returns_n():
    log = "\n".join(
        f"## [2026-0{i}-01] Decisão {i}\n**Contexto:** x\n**Decisão:** y"
        for i in range(1, 8)
    )
    result = _extract_last_decisions(log, n=5)
    entries = result.split("\n\n")
    assert len(entries) == 5
    assert "Decisão 7" in result
    assert "Decisão 1" not in result


def test_extract_last_decisions_fewer_than_n():
    log = "## [2026-01-01] Única decisão\n**Contexto:** x"
    result = _extract_last_decisions(log, n=5)
    assert "Única decisão" in result


@pytest.mark.asyncio
async def test_read_project_context_no_root(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("ARGUS_PROJECT_ROOT", raising=False)
    monkeypatch.chdir("/")
    from argus_mcp.tools.context import _read_project_context
    result = await _read_project_context({})
    assert result.startswith("[ERRO]")


@pytest.mark.asyncio
async def test_read_spec_missing_args():
    from argus_mcp.tools.context import _read_spec
    result = await _read_spec({})
    assert result == "[ERRO] forneça id ou path"
