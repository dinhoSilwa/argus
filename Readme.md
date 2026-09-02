# Argus

> Instala um sistema de engenharia completo em qualquer projeto — em dois minutos.

**[→ Guia completo: como funciona e como usar](docs/guide.md)**

```bash
npx create-argus
```

## O que é

Argus é um CLI + MCP server que configura o ambiente de desenvolvimento inteiro e ensina o agente de IA a operar dentro dele. Não é um gerador de código one-shot — é um sistema instalável.

## O que instala

- Vault SDD (Spec Driven Development) com 13 seções de documentação
- Instruções do agente customizadas para a stack escolhida
- Skills de lint, migração e revisão de endpoints
- MCP server com 11 ferramentas para o agente usar durante o desenvolvimento

## Stacks suportadas

| Stack | Tecnologias |
|-------|-------------|
| `fastapi-supabase` | FastAPI + Supabase (Python) |
| `nextjs-prisma` | Next.js + Prisma (TypeScript) |
| `go-postgres` | Go + PostgreSQL |

## Estrutura do repo

```
argus/
├── packages/
│   ├── cli/    ← TypeScript — distribuído via npm
│   └── mcp/    ← Python — distribuído via PyPI
└── .github/
    └── workflows/
        ├── ci.yml       ← testes em PRs
        └── publish.yml  ← publica ao criar tag vX.Y.Z
```

## Release

```bash
# 1. Atualizar versão em packages/cli/package.json e packages/mcp/pyproject.toml
# 2. Criar e fazer push da tag
git tag v1.0.0
git push origin v1.0.0
# CI publica automaticamente para npm e PyPI
```

## MCP tools disponíveis

| Tool | Descrição |
|------|-----------|
| `read_project_context` | Contexto consolidado do projeto |
| `read_spec` | Lê spec do vault por ID ou path |
| `save_decision` | Registra decisão técnica |
| `update_backlog` | Move item do backlog |
| `create_spec` | Cria nova spec no vault |
| `create_feature` | Scaffolda feature VSA |
| `create_endpoint` | Adiciona endpoint a uma feature |
| `create_migration` | Cria migration numerada |
| `validate_architecture` | Verifica imports cruzados entre features |
| `check_quality` | Lint + typecheck + testes |
| `review_endpoint` | Checklist de endpoint completo |

## Licença

MIT
