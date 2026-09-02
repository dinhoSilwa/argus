import { mkdir, readFile } from "node:fs/promises";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import { registerAgent } from "../src/registry.js";

describe("registerAgent", () => {
  it("não faz nada para agentType none", async () => {
    await expect(
      registerAgent("none", "/tmp/proj", "/tmp/vault")
    ).resolves.toBeUndefined();
  });

  it("cria .cursor/mcp.json para cursor", async () => {
    const { mkdtemp } = await import("node:fs/promises");
    const { tmpdir } = await import("node:os");
    const projectRoot = await mkdtemp(join(tmpdir(), "argus-test-"));

    await registerAgent("cursor", projectRoot, join(projectRoot, "vault"));

    const configPath = join(projectRoot, ".cursor", "mcp.json");
    const content = JSON.parse(await readFile(configPath, "utf-8")) as {
      mcpServers: { argus: { command: string; env: Record<string, string> } };
    };

    expect(content.mcpServers.argus.command).toBe("argus-mcp");
    expect(content.mcpServers.argus.env.ARGUS_PROJECT_ROOT).toBe(projectRoot);
  });
});
