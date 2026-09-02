import { mkdir, readFile, writeFile } from "node:fs/promises";
import { existsSync } from "node:fs";
import { dirname, join } from "node:path";
import { homedir } from "node:os";
import { execFile } from "node:child_process";
import { promisify } from "node:util";
import type { AgentType } from "./wizard.js";

const exec = promisify(execFile);

export async function installMcpServer(): Promise<void> {
  await exec("uv", ["tool", "install", "argus-mcp"]);
}

export async function registerAgent(
  agentType: AgentType,
  projectRoot: string,
  vaultPath: string
): Promise<void> {
  if (agentType === "none") return;

  const entry = {
    command: "argus-mcp",
    env: {
      ARGUS_PROJECT_ROOT: projectRoot,
      ARGUS_VAULT_PATH: vaultPath,
    },
  };

  if (agentType === "claude") {
    await mergeClaudeConfig(entry);
  } else if (agentType === "cursor") {
    await mergeCursorConfig(projectRoot, entry);
  }
}

async function mergeClaudeConfig(entry: object): Promise<void> {
  const configPath = join(homedir(), ".claude", "settings.json");
  const config = await readJson(configPath);
  config.mcpServers ??= {};
  (config.mcpServers as Record<string, object>).argus = entry;
  await writeJson(configPath, config);
}

async function mergeCursorConfig(projectRoot: string, entry: object): Promise<void> {
  const configPath = join(projectRoot, ".cursor", "mcp.json");
  const config = await readJson(configPath);
  config.mcpServers ??= {};
  (config.mcpServers as Record<string, object>).argus = entry;
  await writeJson(configPath, config);
}

async function readJson(filePath: string): Promise<Record<string, unknown>> {
  if (!existsSync(filePath)) return {};
  try {
    return JSON.parse(await readFile(filePath, "utf-8")) as Record<string, unknown>;
  } catch {
    return {};
  }
}

async function writeJson(filePath: string, data: unknown): Promise<void> {
  await mkdir(dirname(filePath), { recursive: true });
  await writeFile(filePath, JSON.stringify(data, null, 2), "utf-8");
}
