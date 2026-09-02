# Guia do Argus

## O que é o Argus

Argus é um sistema instalável que transforma qualquer projeto em um ambiente de engenharia completo em dois minutos. Ele não gera código avulso — ele configura a estrutura, a documentação e as ferramentas que fazem o agente de IA trabalhar com qualidade e rastreabilidade do início ao fim.

Quando você roda `npx create-argus`, três coisas acontecem:

1. **Seu projeto recebe uma estrutura** — vault de documentação, arquitetura VSA, skills de qualidade
2. **O agente de IA aprende as regras do projeto** — via instruções instaladas e MCP server
3. **O agente passa a ter ferramentas especializadas** — 11 ferramentas MCP para scaffoldar, validar e documentar

---

## Pré-requisitos

| Ferramenta | Versão mínima | Para quê |
|-----------|--------------|---------|
| Node.js | 22+ | Rodar o CLI |
| Python | 3.12+ | MCP server |
| uv | qualquer | Instalar o MCP server |
| Claude Code ou Cursor | qualquer | Agente de IA |

**Instalar uv:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

---

## Início rápido

```bash
# Navegue até o diretório do seu projeto
cd meu-projeto

# Rode o Argus
npx create-argus
```

O wizard faz quatro perguntas:

```
? Nome do projeto: meu-projeto
? Stack:
  ❯ FastAPI + Supabase  (Python)
    Next.js + Prisma    (TypeScript)
    Go + PostgreSQL

? Onde instalar o vault: ./vault
? Agente de IA:
  ❯ Claude Code
    Cursor
    Nenhum (configurar manualmente)
```

Em seguida, o Argus:
- Baixa os templates da stack escolhida
- Copia os arquivos para o projeto (sem sobrescrever nada existente)
- Instala o MCP server (`argus-mcp`) via uv
- Configura o agente de IA automaticamente

---

## O que fica no seu projeto

```
meu-projeto/
├── .argus/
│   └── config.json           ← stack e nome do projeto
├── CLAUDE.md                 ← instruções do agente (lidas automaticamente)
├── src/
│   └── features/             ← estrutura VSA, pronta pra usar
├── migrations/               ← diretório de migrações
└── vault/                    ← documentação SDD do projeto
    ├── 00-project-charter/
    │   ├── overview.md       ← visão geral do projeto
    │   └── decision-log.md   ← registro de decisões técnicas
    ├── 01-product/
    │   └── prd.md
    ├── 02-domain/
    │   └── glossary.md
    ├── 03-specifications/
    │   └── backlog.md        ← backlog único do projeto
    ├── 04-architecture/
    │   └── overview.md
    ├── 05-data/
    │   └── schema.md
    ├── 06-security/
    │   └── security.md
    ├── 07-quality/
    │   └── quality.md
    ├── 08-observability/
    │   └── observability.md
    ├── 09-infra/
    │   └── infra.md
    ├── 10-implementation/
    │   └── log.md
    ├── 11-ai-context/
    │   └── instrucao-ia.md   ← primeira coisa que o agente lê
    └── 99-templates/
        └── spec.md           ← template para novas specs
```

---

## Como o agente usa o Argus

O MCP server expõe 11 ferramentas que o agente usa durante o desenvolvimento. Você não precisa chamá-las diretamente — o agente as usa automaticamente conforme trabalha.

### Início de sessão

Toda sessão começa com o agente lendo o contexto do projeto:

```
Agente chama: read_project_context
Recebe: stack, backlog em andamento, últimas 5 decisões, instruções
```

### Durante o desenvolvimento

**Scaffoldar uma nova feature:**
```
Usuário: "crie a feature de autenticação"
Agente chama: create_feature { name: "auth" }

Resultado em src/features/auth/:
  + router.py / page.tsx / handler.go  (conforme a stack)
  + service.py / actions.ts / service.go
  + repository.py / repository.ts / repository.go
  + schemas.py / schemas.ts / model.go
  + tests/
```

**Adicionar um endpoint:**
```
Agente chama: create_endpoint { feature: "auth", method: "POST", path: "/login" }
```

**Criar uma migração:**
```
Agente chama: create_migration { description: "add_users_table" }

Cria:
  migrations/0001_add_users_table.up.sql
  migrations/0001_add_users_table.down.sql
```

**Registrar uma decisão técnica:**
```
Agente chama: save_decision {
  title: "JWT com refresh token",
  context: "precisamos de sessões longas",
  decision: "JWT de curta duração + refresh token no banco",
  reason: "segurança sem comprometer UX"
}

Resultado: entrada adicionada em vault/00-project-charter/decision-log.md
```

**Atualizar o backlog:**
```
Agente chama: update_backlog { id: "FEAT-001", action: "complete" }
```

### Antes de commitar

**Verificar qualidade:**
```
Agente chama: check_quality
Recebe:
  Qualidade OK
    lint:      PASSOU
    typecheck: PASSOU
    testes:    PASSOU (42 passed em 3.2s)
```

**Revisar um endpoint:**
```
Agente chama: review_endpoint { feature: "auth", path: "/login" }
Recebe:
  Endpoint aprovado: POST /login em auth
    ✓ schema Pydantic definido
    ✓ rota registrada
    ✓ lógica no service, não no handler
    ✓ acesso ao banco via repository
    ✓ teste presente
    ✓ sem detalhes internos na resposta de erro
```

**Validar arquitetura:**
```
Agente chama: validate_architecture
Recebe:
  Arquitetura válida.
  Analisadas: 5 features
  Imports cruzados: nenhum
```

---

## Skills instaladas

Cada stack vem com skills que você pode invocar diretamente no agente:

### `/lint-fix`
Corrige lint, tipos e confirma testes antes de qualquer commit.

**FastAPI:** `ruff check --fix` → `ruff format` → `mypy` → `pytest`
**Next.js:** `pnpm lint --fix` → `pnpm type-check` → `pnpm test`
**Go:** `go vet` → `golangci-lint run` → `go test`

### `/migration-checklist`
Garante que toda mudança de schema passa pelos 5 passos obrigatórios: schema → migration → repository → testes → documentação.

### `/endpoint-review` (FastAPI) / `/component-review` (Next.js) / `/handler-review` (Go)
Checklist completo antes de considerar um endpoint/componente/handler como pronto.

---

## Comandos do CLI

### `npx create-argus`
Configura um projeto do zero. Roda uma vez.

### `argus add skill <nome>`
Adiciona uma skill avulsa ao projeto.

```bash
npx create-argus add skill lint-fix
```

Baixa a skill da stack do projeto e instala em `.claude/skills/` ou `.cursor/rules/`.

### `argus sync`
Atualiza os templates para a versão mais recente, preservando arquivos que você modificou.

```bash
npx create-argus sync              # atualiza para "latest"
npx create-argus sync --ref v1.2.0 # versão específica
```

---

## Arquitetura VSA

Argus usa Vertical Slice Architecture como padrão. Cada feature é autossuficiente:

```
src/features/
└── pagamentos/
    ├── router.py       ← endpoints (FastAPI) / page.tsx (Next.js) / handler.go (Go)
    ├── service.py      ← lógica de negócio (nunca conhece HTTP)
    ├── repository.py   ← acesso ao banco (nunca conhece HTTP)
    ├── schemas.py      ← tipos de entrada e saída
    └── tests/
        └── test_pagamentos.py
```

**Regra fundamental:** features nunca importam umas das outras diretamente. Dependências entre features vão via serviço, nunca via import direto de repository. O agente detecta violações com `validate_architecture`.

---

## Metodologia SDD

O vault segue Spec Driven Development — toda implementação referencia uma spec. O fluxo é:

```
Problema identificado
  └── spec criada no vault (create_spec ou manual)
      └── item adicionado ao backlog
          └── implementação referencia o ID da spec
              └── task concluída → backlog atualizado + decisão salva se relevante
```

Isso garante rastreabilidade total entre o problema, a decisão e o código.

---

## Configuração manual do MCP server

Se você escolheu "Nenhum" no wizard ou quer configurar manualmente:

**Claude Code** — adicione em `~/.claude/settings.json`:
```json
{
  "mcpServers": {
    "argus": {
      "command": "argus-mcp",
      "env": {
        "ARGUS_PROJECT_ROOT": "/caminho/absoluto/do/projeto",
        "ARGUS_VAULT_PATH": "/caminho/absoluto/do/vault"
      }
    }
  }
}
```

**Cursor** — crie `.cursor/mcp.json` na raiz do projeto:
```json
{
  "mcpServers": {
    "argus": {
      "command": "argus-mcp",
      "env": {
        "ARGUS_PROJECT_ROOT": "/caminho/absoluto/do/projeto",
        "ARGUS_VAULT_PATH": "/caminho/absoluto/do/vault"
      }
    }
  }
}
```

---

## Variáveis de ambiente do MCP server

| Variável | Obrigatório | Descrição |
|----------|-------------|-----------|
| `ARGUS_PROJECT_ROOT` | não* | Raiz do projeto. Se omitido, sobe a árvore procurando `.argus/` ou `CLAUDE.md` |
| `ARGUS_VAULT_PATH` | não* | Caminho do vault. Se omitido, usa `PROJECT_ROOT/vault` |

*Recomendado definir explicitamente para evitar ambiguidades em workspaces com múltiplos projetos.

---

## Perguntas frequentes

**O Argus sobrescreve meus arquivos?**
Não. O installer pula qualquer arquivo que já existe no projeto. O `argus sync` compara hashes e preserva arquivos modificados.

**Posso usar em projetos que já existem?**
Sim. O Argus detecta o que já existe e instala apenas o que está faltando.

**Funciona sem internet?**
O MCP server funciona completamente offline. O CLI precisa de internet na primeira instalação para baixar os templates, depois usa cache local em `~/.argus/cache/`.

**Como atualizo o MCP server?**
```bash
uv tool upgrade argus-mcp-cli
```

**Posso ter múltiplos projetos com Argus?**
Sim. Cada projeto tem seu próprio `ARGUS_PROJECT_ROOT` e `ARGUS_VAULT_PATH` na configuração do MCP server.
