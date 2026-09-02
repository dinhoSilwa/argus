import { input, select } from "@inquirer/prompts";
import { basename } from "node:path";

export type Stack = "fastapi-supabase" | "nextjs-prisma" | "go-postgres";
export type AgentType = "claude" | "cursor" | "none";

export interface Config {
  projectName: string;
  stack: Stack;
  vaultPath: string;
  agentType: AgentType;
  templatesRef: string;
}

export async function wizard(): Promise<Config> {
  const projectName = await input({
    message: "Nome do projeto:",
    default: basename(process.cwd()),
    validate: (v) => v.trim().length > 0 || "Nome não pode ser vazio",
  });

  const stack = await select<Stack>({
    message: "Stack:",
    choices: [
      { value: "fastapi-supabase", name: "FastAPI + Supabase  (Python)" },
      { value: "nextjs-prisma",    name: "Next.js + Prisma    (TypeScript)" },
      { value: "go-postgres",      name: "Go + PostgreSQL" },
    ],
  });

  const vaultPath = await input({
    message: "Onde instalar o vault:",
    default: "./vault",
  });

  const agentType = await select<AgentType>({
    message: "Agente de IA:",
    choices: [
      { value: "claude", name: "Claude Code" },
      { value: "cursor", name: "Cursor" },
      { value: "none",   name: "Nenhum (configurar manualmente)" },
    ],
  });

  return {
    projectName: projectName.trim(),
    stack,
    vaultPath,
    agentType,
    templatesRef: "latest",
  };
}
