from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from argus_mcp.tools.validate import _find_cross_imports, _imports_feature


def test_imports_feature_python_detects_cross():
    content = "from features.billing.repository import get"
    assert _imports_feature(content, "billing", ".py") is True


def test_imports_feature_python_same_feature():
    content = "from features.payments.service import create"
    assert _imports_feature(content, "billing", ".py") is False


def test_imports_feature_ts_detects_cross():
    content = 'import { get } from "@/features/billing/repository"'
    assert _imports_feature(content, "billing", ".ts") is True


def test_no_cross_imports(tmp_path: Path):
    features = tmp_path / "features"
    (features / "payments").mkdir(parents=True)
    (features / "billing").mkdir(parents=True)
    (features / "payments" / "service.py").write_text("from app.db import get_db\n")
    violations = _find_cross_imports(features, ["payments", "billing"])
    assert violations == []


def test_cross_import_detected(tmp_path: Path):
    features = tmp_path / "features"
    (features / "payments").mkdir(parents=True)
    (features / "billing").mkdir(parents=True)
    (features / "payments" / "service.py").write_text(
        "from features.billing.repository import get\n"
    )
    violations = _find_cross_imports(features, ["payments", "billing"])
    assert len(violations) == 1
    assert "billing" in violations[0][1]


def _setup(tmp_path: Path, stack: str) -> None:
    (tmp_path / ".argus").mkdir()
    (tmp_path / ".argus" / "config.json").write_text(json.dumps({"stack": stack}))
    vault = tmp_path / "vault"
    vault.mkdir()
    os.environ["ARGUS_PROJECT_ROOT"] = str(tmp_path)
    os.environ["ARGUS_VAULT_PATH"] = str(vault)


def _teardown() -> None:
    os.environ.pop("ARGUS_PROJECT_ROOT", None)
    os.environ.pop("ARGUS_VAULT_PATH", None)


@pytest.mark.asyncio
async def test_validate_architecture_no_features(tmp_path: Path):
    _setup(tmp_path, "fastapi-supabase")
    try:
        from argus_mcp.tools.validate import _validate_architecture
        result = await _validate_architecture({})
        assert result.startswith("[ERRO]")
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_validate_architecture_clean(tmp_path: Path):
    _setup(tmp_path, "fastapi-supabase")
    (tmp_path / "src" / "features" / "payments").mkdir(parents=True)
    (tmp_path / "src" / "features" / "payments" / "service.py").write_text("")
    try:
        from argus_mcp.tools.validate import _validate_architecture
        result = await _validate_architecture({})
        assert "válida" in result
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_review_endpoint_fastapi_complete(tmp_path: Path):
    _setup(tmp_path, "fastapi-supabase")
    feature = tmp_path / "src" / "features" / "users"
    feature.mkdir(parents=True)
    for f in ["schemas.py", "router.py", "service.py", "repository.py"]:
        (feature / f).write_text("")
    (feature / "tests").mkdir()
    (feature / "tests" / "test_users.py").write_text("")
    try:
        from argus_mcp.tools.validate import _review_endpoint
        result = await _review_endpoint({"feature": "users", "path": "/users"})
        assert "aprovado" in result
        assert "✗" not in result
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_review_endpoint_missing_test(tmp_path: Path):
    _setup(tmp_path, "fastapi-supabase")
    feature = tmp_path / "src" / "features" / "users"
    feature.mkdir(parents=True)
    for f in ["schemas.py", "router.py", "service.py", "repository.py"]:
        (feature / f).write_text("")
    try:
        from argus_mcp.tools.validate import _review_endpoint
        result = await _review_endpoint({"feature": "users", "path": "/users"})
        assert "incompleto" in result
        assert "✗ teste" in result
    finally:
        _teardown()
