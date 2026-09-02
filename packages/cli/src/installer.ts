import { mkdir, readFile, writeFile } from "node:fs/promises";
import { existsSync } from "node:fs";
import { dirname, join, relative } from "node:path";
import { glob } from "node:fs/promises";

export interface InstallOptions {
  projectName: string;
  stack: string;
  date?: string;
}

export async function install(
  srcDir: string,
  destDir: string,
  options: InstallOptions
): Promise<string[]> {
  const { projectName, stack, date = new Date().toISOString().slice(0, 10) } = options;
  const created: string[] = [];
  const skipped: string[] = [];

  for await (const src of glob("**/*", { cwd: srcDir })) {
    const srcPath = join(srcDir, src);
    const destPath = join(destDir, src);

    if (existsSync(destPath)) {
      skipped.push(src);
      continue;
    }

    const content = await readFile(srcPath, "utf-8").catch(() => null);
    if (content === null) continue; // directory or binary

    const replaced = applyPlaceholders(content, { projectName, stack, date });
    await mkdir(dirname(destPath), { recursive: true });
    await writeFile(destPath, replaced, "utf-8");
    created.push(relative(destDir, destPath));
  }

  await writeArgusConfig(destDir, { projectName, stack });

  if (skipped.length > 0) {
    console.warn(`\n[aviso] ${skipped.length} arquivo(s) já existem e foram mantidos.`);
  }

  return created;
}

export function applyPlaceholders(
  content: string,
  vars: { projectName: string; stack: string; date: string }
): string {
  return content
    .replaceAll("{{PROJECT_NAME}}", vars.projectName)
    .replaceAll("{{STACK}}", vars.stack)
    .replaceAll("{{DATE}}", vars.date);
}

async function writeArgusConfig(
  projectRoot: string,
  data: { projectName: string; stack: string }
): Promise<void> {
  const argusDir = join(projectRoot, ".argus");
  await mkdir(argusDir, { recursive: true });
  await writeFile(
    join(argusDir, "config.json"),
    JSON.stringify(data, null, 2),
    "utf-8"
  );
}
