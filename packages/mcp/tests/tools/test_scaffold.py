from __future__ import annotations

import os
from pathlib import Path

import pytest

from argus_mcp.tools.scaffold import _next_migration_number, _pascal, _feature_files


def test_pascal():
    assert _pascal("user-auth") == "UserAuth"
    assert _pascal("my_feature") == "MyFeature"
    assert _pascal("example") == "Example"


def test_next_migration_number_empty(tmp_path: Path):
    assert _next_migration_number(tmp_path) == 1


def test_next_migration_number_existing(tmp_path: Path):
    (tmp_path / "0001_init.up.sql").touch()
    (tmp_path / "0003_add_col.up.sql").touch()
    assert _next_migration_number(tmp_path) == 4


def test_feature_files_fastapi():
    files = _feature_files("fastapi-supabase", "user-auth")
    assert "router.py" in files
    assert "service.py" in files
    assert "repository.py" in files
    assert "schemas.py" in files
    assert any("test_" in k for k in files)


def test_feature_files_nextjs():
    files = _feature_files("nextjs-prisma", "dashboard")
    assert "page.tsx" in files
    assert "actions.ts" in files


def test_feature_files_go():
    files = _feature_files("go-postgres", "billing")
    assert "handler.go" in files
    assert "service.go" in files


def _setup_env(tmp_path: Path, stack: str) -> None:
    (tmp_path / ".argus").mkdir()
    import json
    (tmp_path / ".argus" / "config.json").write_text(json.dumps({"stack": stack}))
    vault = tmp_path / "vault"
    (vault / "03-specifications").mkdir(parents=True)
    (vault / "99-templates").mkdir(parents=True)
    (vault / "11-ai-context").mkdir(parents=True)
    os.environ["ARGUS_PROJECT_ROOT"] = str(tmp_path)
    os.environ["ARGUS_VAULT_PATH"] = str(vault)


def _teardown_env() -> None:
    os.environ.pop("ARGUS_PROJECT_ROOT", None)
    os.environ.pop("ARGUS_VAULT_PATH", None)


@pytest.mark.asyncio
async def test_create_spec(tmp_path: Path):
    _setup_env(tmp_path, "fastapi-supabase")
    try:
        from argus_mcp.tools.scaffold import _create_spec
        result = await _create_spec({"id": "PROJ-001", "title": "My Feature"})
        assert "Spec criada" in result
        assert (tmp_path / "vault" / "03-specifications" / "PROJ-001-my-feature.md").exists()
    finally:
        _teardown_env()


@pytest.mark.asyncio
async def test_create_spec_already_exists(tmp_path: Path):
    _setup_env(tmp_path, "fastapi-supabase")
    try:
        from argus_mcp.tools.scaffold import _create_spec
        await _create_spec({"id": "PROJ-001", "title": "My Feature"})
        result = await _create_spec({"id": "PROJ-001", "title": "My Feature"})
        assert result.startswith("[ERRO]")
    finally:
        _teardown_env()


@pytest.mark.asyncio
async def test_create_feature_fastapi(tmp_path: Path):
    _setup_env(tmp_path, "fastapi-supabase")
    try:
        from argus_mcp.tools.scaffold import _create_feature
        result = await _create_feature({"name": "payments"})
        assert "Feature criada" in result
        assert (tmp_path / "src" / "features" / "payments" / "router.py").exists()
    finally:
        _teardown_env()


@pytest.mark.asyncio
async def test_create_migration(tmp_path: Path):
    _setup_env(tmp_path, "fastapi-supabase")
    try:
        from argus_mcp.tools.scaffold import _create_migration
        result = await _create_migration({"description": "add_users_table"})
        assert "Migration criada" in result
        assert (tmp_path / "migrations" / "0001_add_users_table.up.sql").exists()
        assert (tmp_path / "migrations" / "0001_add_users_table.down.sql").exists()
    finally:
        _teardown_env()
