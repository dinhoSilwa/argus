import { mkdir, writeFile } from "node:fs/promises";
import { existsSync } from "node:fs";
import { join } from "node:path";
import { beforeEach, describe, expect, it } from "vitest";
import { applyPlaceholders, install } from "../src/installer.js";

const VARS = { projectName: "my-app", stack: "fastapi-supabase", date: "2026-09-02" };

describe("applyPlaceholders", () => {
  it("substitui todos os placeholders", () => {
    const result = applyPlaceholders(
      "Projeto: {{PROJECT_NAME}} | Stack: {{STACK}} | Data: {{DATE}}",
      VARS
    );
    expect(result).toBe("Projeto: my-app | Stack: fastapi-supabase | Data: 2026-09-02");
  });

  it("substitui múltiplas ocorrências", () => {
    const result = applyPlaceholders("{{PROJECT_NAME}} e {{PROJECT_NAME}}", VARS);
    expect(result).toBe("my-app e my-app");
  });

  it("mantém texto sem placeholders", () => {
    const result = applyPlaceholders("sem placeholders", VARS);
    expect(result).toBe("sem placeholders");
  });
});

describe("install", () => {
  let src: string;
  let dest: string;

  beforeEach(async (ctx) => {
    const base = (ctx as { task: { id: string } }).task.id.replace(/\W/g, "_");
    src = join(import.meta.dirname, `__tmp_src_${base}`);
    dest = join(import.meta.dirname, `__tmp_dest_${base}`);
    await mkdir(src, { recursive: true });
    await mkdir(dest, { recursive: true });
  });

  it("cria arquivos com placeholders substituídos", async () => {
    await writeFile(join(src, "README.md"), "# {{PROJECT_NAME}}");
    const created = await install(src, dest, VARS);
    expect(created).toContain("README.md");
    const { readFile } = await import("node:fs/promises");
    const content = await readFile(join(dest, "README.md"), "utf-8");
    expect(content).toBe("# my-app");
  });

  it("não sobrescreve arquivos existentes", async () => {
    await writeFile(join(src, "config.md"), "novo");
    await writeFile(join(dest, "config.md"), "original");
    await install(src, dest, VARS);
    const { readFile } = await import("node:fs/promises");
    const content = await readFile(join(dest, "config.md"), "utf-8");
    expect(content).toBe("original");
  });

  it("cria .argus/config.json", async () => {
    await install(src, dest, VARS);
    expect(existsSync(join(dest, ".argus", "config.json"))).toBe(true);
  });
});
