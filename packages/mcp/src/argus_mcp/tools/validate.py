from __future__ import annotations

import asyncio
import re
from pathlib import Path

import mcp.types as types

from argus_mcp.config import load

TOOLS: list[types.Tool] = [
    types.Tool(
        name="validate_architecture",
        description="Verifica se a estrutura do projeto segue VSA (sem imports cruzados entre features).",
        inputSchema={"type": "object", "properties": {}},
    ),
    types.Tool(
        name="check_quality",
        description="Executa lint + typecheck + testes e retorna resultado consolidado.",
        inputSchema={
            "type": "object",
            "properties": {
                "fix": {"type": "boolean", "description": "Tenta corrigir automaticamente"},
            },
        },
    ),
    types.Tool(
        name="review_endpoint",
        description="Verifica checklist de endpoint completo.",
        inputSchema={
            "type": "object",
            "properties": {
                "feature": {"type": "string"},
                "path": {"type": "string"},
            },
            "required": ["feature", "path"],
        },
    ),
]


async def _validate_architecture(args: dict[str, object]) -> str:
    try:
        cfg = load()
    except RuntimeError as e:
        return f"[ERRO] {e}"

    features_dir = cfg.project_root / "src" / "features"
    if not features_dir.exists():
        return "[ERRO] src/features/ não encontrado — rode create_feature primeiro"

    features = [d.name for d in features_dir.iterdir() if d.is_dir()]
    violations = _find_cross_imports(features_dir, features)

    if not violations:
        return (
            f"Arquitetura válida.\n"
            f"Analisadas: {len(features)} features\n"
            f"Imports cruzados: nenhum"
        )

    lines = ["[AVISO] Imports cruzados detectados:"]
    lines.extend(f"  {src} → {dst}" for src, dst in violations)
    return "\n".join(lines)


async def _check_quality(args: dict[str, object]) -> str:
    try:
        cfg = load()
    except RuntimeError as e:
        return f"[ERRO] {e}"

    fix = bool(args.get("fix", False))
    stack = cfg.stack
    commands = _quality_commands(stack, fix, cfg.project_root)

    results: list[tuple[str, bool, str]] = []
    for label, cmd in commands:
        ok, output = await _run(cmd, cwd=cfg.project_root)
        results.append((label, ok, output))

    all_passed = all(ok for _, ok, _ in results)
    header = "Qualidade OK" if all_passed else "[ERRO] Qualidade falhou"
    lines = [header]
    for label, ok, output in results:
        status = "PASSOU" if ok else "FALHOU"
        lines.append(f"  {label:<12} {status}")
        if not ok:
            lines.extend(f"    {l}" for l in output.strip().splitlines()[:10])

    return "\n".join(lines)


async def _review_endpoint(args: dict[str, object]) -> str:
    try:
        cfg = load()
    except RuntimeError as e:
        return f"[ERRO] {e}"

    feature = str(args.get("feature", ""))
    path = str(args.get("path", ""))
    feature_dir = cfg.project_root / "src" / "features" / feature

    if not feature_dir.exists():
        return f"[ERRO] feature não encontrada: src/features/{feature}"

    checklist = _build_checklist(feature_dir, cfg.stack)
    all_passed = all(ok for _, ok, _ in checklist)

    status = "aprovado" if all_passed else "incompleto"
    header = f"Endpoint {status}: {path} em {feature}"
    lines = [header]
    for item, ok, note in checklist:
        mark = "✓" if ok else "✗"
        line = f"  {mark} {item}"
        if note:
            line += f" — {note}"
        lines.append(line)

    return "\n".join(lines)


# --- helpers ---

def _find_cross_imports(
    features_dir: Path, features: list[str]
) -> list[tuple[str, str]]:
    violations: list[tuple[str, str]] = []
    for feature in features:
        feature_path = features_dir / feature
        for src_file in feature_path.rglob("*"):
            if src_file.suffix not in (".py", ".ts", ".tsx", ".go"):
                continue
            try:
                content = src_file.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            for other in features:
                if other == feature:
                    continue
                if _imports_feature(content, other, src_file.suffix):
                    rel = src_file.relative_to(features_dir.parent.parent)
                    violations.append((str(rel), f"features/{other}"))
    return violations


def _imports_feature(content: str, other_feature: str, suffix: str) -> bool:
    snake = other_feature.replace("-", "_")
    if suffix == ".py":
        return bool(re.search(rf"from features\.{snake}\.|import features\.{snake}", content))
    if suffix in (".ts", ".tsx"):
        return bool(re.search(rf"from ['\"].*features/{other_feature}", content))
    if suffix == ".go":
        return bool(re.search(rf"\".*features/{other_feature}\"", content))
    return False


def _quality_commands(
    stack: str, fix: bool, root: Path
) -> list[tuple[str, list[str]]]:
    if "fastapi" in stack or "python" in stack:
        lint_cmd = ["ruff", "check", ".", "--fix"] if fix else ["ruff", "check", "."]
        return [
            ("lint", lint_cmd),
            ("typecheck", ["mypy", "src/"]),
            ("testes", ["pytest", "--tb=short", "-q"]),
        ]
    if "nextjs" in stack or "next" in stack:
        lint_cmd = ["pnpm", "lint", "--fix"] if fix else ["pnpm", "lint"]
        return [
            ("lint", lint_cmd),
            ("typecheck", ["pnpm", "type-check"]),
            ("testes", ["pnpm", "test", "--run"]),
        ]
    if "go" in stack:
        return [
            ("vet", ["go", "vet", "./..."]),
            ("lint", ["golangci-lint", "run", "./..."]),
            ("testes", ["go", "test", "./..."]),
        ]
    return [("testes", ["echo", "stack não reconhecida"])]


async def _run(cmd: list[str], cwd: Path) -> tuple[bool, str]:
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=cwd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=60)
        output = stdout.decode(errors="replace")
        return proc.returncode == 0, output
    except FileNotFoundError:
        return False, f"[comando não encontrado: {cmd[0]}]"
    except asyncio.TimeoutError:
        return False, "[timeout após 60s]"


def _build_checklist(
    feature_dir: Path, stack: str
) -> list[tuple[str, bool, str]]:
    files = {f.name for f in feature_dir.rglob("*") if f.is_file()}
    has_test = any("test" in f.lower() for f in files)

    if "fastapi" in stack or "python" in stack:
        return [
            ("schema Pydantic definido", "schemas.py" in files, ""),
            ("rota em router.py", "router.py" in files, ""),
            ("lógica no service.py", "service.py" in files, ""),
            ("acesso ao banco via repository.py", "repository.py" in files, ""),
            ("teste presente", has_test, "crie em tests/"),
        ]
    if "nextjs" in stack or "next" in stack:
        return [
            ("schema Zod definido", "schemas.ts" in files, ""),
            ("server action em actions.ts", "actions.ts" in files, ""),
            ("acesso ao banco via repository.ts", "repository.ts" in files, ""),
            ("page.tsx presente", "page.tsx" in files, ""),
            ("teste presente", has_test, "crie em tests/"),
        ]
    if "go" in stack:
        return [
            ("handler.go presente", "handler.go" in files, ""),
            ("service.go presente", "service.go" in files, ""),
            ("repository.go presente", "repository.go" in files, ""),
            ("teste presente", has_test, "crie handler_test.go"),
        ]
    return [("estrutura de feature", feature_dir.exists(), "")]


HANDLERS: dict[str, object] = {
    "validate_architecture": _validate_architecture,
    "check_quality": _check_quality,
    "review_endpoint": _review_endpoint,
}
