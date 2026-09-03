import { createWriteStream } from "node:fs";
import { cp, mkdir, mkdtemp, rm } from "node:fs/promises";
import { homedir, tmpdir } from "node:os";
import { join } from "node:path";
import { pipeline } from "node:stream/promises";
import * as tar from "tar";

const REPO = "dinhoSilwa/argus-templates";
const CACHE_DIR = join(homedir(), ".argus", "cache");

export async function fetchStack(
  stack: string,
  ref: string,
  destDir: string
): Promise<void> {
  const resolved = await resolveRef(ref);
  const cacheRoot = await ensureCache(resolved);
  await cp(join(cacheRoot, "stacks", stack), destDir, { recursive: true });
}

export async function fetchVault(ref: string, destDir: string): Promise<void> {
  const resolved = await resolveRef(ref);
  const cacheRoot = await ensureCache(resolved);
  await cp(join(cacheRoot, "vault"), destDir, { recursive: true });
}

async function resolveRef(ref: string): Promise<string> {
  if (ref !== "latest") return ref;
  try {
    const res = await fetch(
      `https://api.github.com/repos/${REPO}/releases/latest`,
      { headers: { "User-Agent": "argus-cli" } }
    );
    const data = (await res.json()) as { tag_name: string };
    return data.tag_name ?? "main";
  } catch {
    return "main";
  }
}

async function ensureCache(ref: string): Promise<string> {
  const cacheRoot = join(CACHE_DIR, ref);
  try {
    await mkdir(cacheRoot, { recursive: true });
    const marker = join(cacheRoot, ".done");
    const { existsSync } = await import("node:fs");
    if (existsSync(marker)) return cacheRoot;
  } catch {
    // fallback to tmp if cache dir not writable
  }

  await downloadAndExtract(ref, cacheRoot);
  const { writeFile } = await import("node:fs/promises");
  await writeFile(join(cacheRoot, ".done"), "");
  return cacheRoot;
}

async function downloadAndExtract(ref: string, destDir: string): Promise<void> {
  const url = `https://github.com/${REPO}/archive/${ref}.tar.gz`;
  const tmp = await mkdtemp(join(tmpdir(), "argus-"));
  const tarball = join(tmp, "templates.tar.gz");

  try {
    const res = await fetch(url);
    if (!res.ok || !res.body) throw new Error(`HTTP ${res.status}: ${url}`);

    const writer = createWriteStream(tarball);
    await pipeline(res.body as unknown as NodeJS.ReadableStream, writer);

    await mkdir(destDir, { recursive: true });
    await tar.x({
      file: tarball,
      cwd: destDir,
      strip: 1,
      filter: (p: string) =>
        p.includes("/stacks/") ||
        p.includes("/vault/") ||
        p.endsWith("/stacks") ||
        p.endsWith("/vault"),
    });
  } finally {
    await rm(tmp, { recursive: true, force: true });
  }
}
