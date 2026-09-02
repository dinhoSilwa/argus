from __future__ import annotations

import re
from datetime import date
from pathlib import Path
from typing import Any

import mcp.types as types

from argus_mcp.config import load

TOOLS: list[types.Tool] = [
    types.Tool(
        name="create_spec",
        description="Cria um novo arquivo de spec no vault a partir do template.",
        input_schema={
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "title": {"type": "string"},
            },
            "required": ["id", "title"],
        },
    ),
    types.Tool(
        name="create_feature",
        description="Cria estrutura VSA de uma nova feature no projeto.",
        input_schema={
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Nome em kebab-case"},
            },
            "required": ["name"],
        },
    ),
    types.Tool(
        name="create_endpoint",
        description="Cria arquivos de endpoint dentro de uma feature existente.",
        input_schema={
            "type": "object",
            "properties": {
                "feature": {"type": "string"},
                "method": {
                    "type": "string",
                    "enum": ["GET", "POST", "PUT", "PATCH", "DELETE"],
                },
                "path": {"type": "string"},
            },
            "required": ["feature", "method", "path"],
        },
    ),
    types.Tool(
        name="create_migration",
        description="Cria arquivo de migração numerado sequencialmente.",
        input_schema={
            "type": "object",
            "properties": {
                "description": {"type": "string", "description": "Em snake_case"},
            },
            "required": ["description"],
        },
    ),
]


async def _create_spec(args: dict[str, object]) -> str:
    try:
        cfg = load()
    except RuntimeError as e:
        return f"[ERRO] {e}"

    spec_id = str(args.get("id", ""))
    title = str(args.get("title", ""))
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    target = cfg.vault_path / "03-specifications" / f"{spec_id}-{slug}.md"

    if target.exists():
        return f"[ERRO] spec já existe: {target.relative_to(cfg.vault_path)}"

    template_file = cfg.vault_path / "99-templates" / "spec.md"
    if template_file.exists():
        content = template_file.read_text(encoding="utf-8")
    else:
        content = _default_spec_template()

    today = date.today().isoformat()
    content = (
        content.replace("PROJ-SPEC-XXX", spec_id)
        .replace("[título]", title)
        .replace("{{DATE}}", today)
    )

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return f"Spec criada: vault/03-specifications/{target.name}"


async def _create_feature(args: dict[str, object]) -> str:
    try:
        cfg = load()
    except RuntimeError as e:
        return f"[ERRO] {e}"

    name = str(args.get("name", "")).strip()
    feature_dir = cfg.project_root / "src" / "features" / name

    if feature_dir.exists():
        return f"[ERRO] feature já existe: src/features/{name}"

    files = _feature_files(cfg.stack, name)
    for rel_path, content in files.items():
        full = feature_dir / rel_path
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_text(content, encoding="utf-8")

    created = "\n".join(f"  + {p}" for p in files)
    return f"Feature criada: src/features/{name}/\n{created}"


async def _create_endpoint(args: dict[str, object]) -> str:
    try:
        cfg = load()
    except RuntimeError as e:
        return f"[ERRO] {e}"

    feature = str(args.get("feature", ""))
    method = str(args.get("method", "GET")).upper()
    path = str(args.get("path", ""))
    feature_dir = cfg.project_root / "src" / "features" / feature

    if not feature_dir.exists():
        return f"[ERRO] feature não encontrada: src/features/{feature}"

    note = _endpoint_note(cfg.stack, method, path)
    return f"Endpoint adicionado: {method} {path} em src/features/{feature}/\n{note}"


async def _create_migration(args: dict[str, object]) -> str:
    try:
        cfg = load()
    except RuntimeError as e:
        return f"[ERRO] {e}"

    description = str(args.get("description", "")).strip()
    migrations_dir = cfg.project_root / "migrations"
    migrations_dir.mkdir(exist_ok=True)

    next_num = _next_migration_number(migrations_dir)
    prefix = f"{next_num:04d}_{description}"

    up_file = migrations_dir / f"{prefix}.up.sql"
    down_file = migrations_dir / f"{prefix}.down.sql"

    up_file.write_text(f"-- Migration: {description}\n\n", encoding="utf-8")
    down_file.write_text(f"-- Rollback: {description}\n\n", encoding="utf-8")

    return (
        f"Migration criada:\n"
        f"  + migrations/{up_file.name}\n"
        f"  + migrations/{down_file.name}"
    )


# --- helpers ---


def _next_migration_number(migrations_dir: Path) -> int:
    existing = [
        int(m.name[:4]) for m in migrations_dir.glob("*.sql") if m.name[:4].isdigit()
    ]
    return max(existing, default=0) + 1


def _feature_files(stack: str, name: str) -> dict[str, str]:
    snake = name.replace("-", "_")
    if "fastapi" in stack or "python" in stack:
        return {
            "schemas.py": f"from pydantic import BaseModel\n\n\nclass {_pascal(name)}Response(BaseModel):\n    pass\n",
            "repository.py": f'from supabase import AsyncClient\n\n\nasync def find_all(db: AsyncClient) -> list[dict]:\n    result = await db.table("{snake}s").select("*").execute()\n    return result.data\n',
            "service.py": "from supabase import AsyncClient\nfrom . import repository\n\n\nasync def list_all(db: AsyncClient) -> list[dict]:\n    return await repository.find_all(db)\n",
            "router.py": f'from fastapi import APIRouter, Depends\nfrom supabase import AsyncClient\nfrom app.deps import get_db\nfrom . import service\n\nrouter = APIRouter(prefix="/{snake}s", tags=["{snake}s"])\n\n\n@router.get("/")\nasync def list_{snake}s(db: AsyncClient = Depends(get_db)):\n    return await service.list_all(db)\n',
            f"tests/test_{snake}.py": f'import pytest\nfrom httpx import AsyncClient\n\n\n@pytest.mark.asyncio\nasync def test_list_{snake}s(client: AsyncClient):\n    response = await client.get("/{snake}s/")\n    assert response.status_code == 200\n',
        }
    if "nextjs" in stack or "next" in stack:
        return {
            "page.tsx": f"export default async function {_pascal(name)}Page() {{\n  return <main><h1>{_pascal(name)}</h1></main>;\n}}\n",
            "actions.ts": f'"use server";\n\nexport async function list{_pascal(name)}() {{\n  // TODO\n  return [];\n}}\n',
            "repository.ts": f'import {{ prisma }} from "@/lib/prisma";\n\nexport async function findAll() {{\n  return prisma.{snake}.findMany();\n}}\n',
            "schemas.ts": f'import {{ z }} from "zod";\n\nexport const {snake}Schema = z.object({{\n  id: z.string(),\n}});\n',
            f"tests/{snake}.test.ts": f'import {{ describe, it, expect }} from "vitest";\n\ndescribe("{name}", () => {{\n  it("placeholder", () => expect(true).toBe(true));\n}});\n',
        }
    if "go" in stack:
        pkg = snake
        return {
            "model.go": f'package {pkg}\n\ntype {_pascal(name)} struct {{\n\tID string `json:"id"`\n}}\n',
            "repository.go": f"package {pkg}\n\ntype Repository struct{{}}\n",
            "service.go": f"package {pkg}\n\ntype Service struct {{\n\trepo *Repository\n}}\n\nfunc NewService(r *Repository) *Service {{ return &Service{{repo: r}} }}\n",
            "handler.go": f'package {pkg}\n\nimport "net/http"\n\ntype Handler struct {{ svc *Service }}\n\nfunc NewHandler(s *Service) *Handler {{ return &Handler{{svc: s}} }}\n\nfunc (h *Handler) List(w http.ResponseWriter, r *http.Request) {{}}\n',
            "handler_test.go": f'package {pkg}_test\n\nimport "testing"\n\nfunc TestList(t *testing.T) {{ t.Skip("implement") }}\n',
        }
    return {
        "README.md": f"# {name}\n\nFeature criada pelo Argus. Stack não reconhecida: {stack}\n"
    }


def _endpoint_note(stack: str, method: str, path: str) -> str:
    if "fastapi" in stack:
        return f'  Adicione @router.{method.lower()}("{path}") em router.py'
    if "nextjs" in stack:
        return f"  Adicione export async function {method.lower()}() em route.ts"
    if "go" in stack:
        return f'  Adicione r.{method}("{path}", h.handler) em handler.go'
    return "  Adicione o handler conforme a stack do projeto"


def _pascal(name: str) -> str:
    return "".join(w.capitalize() for w in re.split(r"[-_]", name))


def _default_spec_template() -> str:
    return """---
id: {{ID}}
title: Spec — {{TITLE}}
type: spec
status: draft
created_at: {{DATE}}
updated_at: {{DATE}}
---

# Spec — {{TITLE}}

## Contexto

## Comportamento esperado

## Critérios de aceitação

- [ ] ...

## Fora de escopo

- ...
"""


HANDLERS: dict[str, Any] = {
    "create_spec": _create_spec,
    "create_feature": _create_feature,
    "create_endpoint": _create_endpoint,
    "create_migration": _create_migration,
}
