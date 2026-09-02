import { mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import ora from "ora";
import { fetchStack, fetchVault } from "../fetcher.js";
import { install } from "../installer.js";
import { installMcpServer, registerAgent } from "../registry.js";
import { wizard } from "../wizard.js";

export async function init(): Promise<void> {
  console.log("\nArgus — configuração do projeto\n");

  const config = await wizard();
  const projectRoot = process.cwd();
  const vaultDest = join(projectRoot, config.vaultPath);
  const tmp = await mkdtemp(join(tmpdir(), "argus-init-"));

  try {
    const spinner = ora("Baixando templates...").start();
    await fetchStack(config.stack, config.templatesRef, join(tmp, "stack"));
    await fetchVault(config.templatesRef, join(tmp, "vault"));
    spinner.succeed("Templates baixados");

    spinner.start("Instalando arquivos...");
    const stackFiles = await install(join(tmp, "stack"), projectRoot, config);
    const vaultFiles = await install(join(tmp, "vault"), vaultDest, config);
    spinner.succeed(`${stackFiles.length + vaultFiles.length} arquivos instalados`);

    spinner.start("Configurando agente de IA...");
    await installMcpServer();
    await registerAgent(config.agentType, projectRoot, vaultDest);
    spinner.succeed("MCP server configurado");

    console.log(`
Projeto "${config.projectName}" pronto!

Próximos passos:
  1. Abra o projeto no seu agente de IA
  2. O agente já conhece o projeto via MCP server (tool: read_project_context)
  3. Consulte ${config.vaultPath}/11-ai-context/instrucao-ia.md para orientações
`);
  } finally {
    await rm(tmp, { recursive: true, force: true });
  }
}
