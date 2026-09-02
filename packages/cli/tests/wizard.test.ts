import { describe, it, expect, vi, beforeEach } from "vitest";

vi.mock("@inquirer/prompts", () => ({
  input: vi.fn(),
  select: vi.fn(),
}));

import { input, select } from "@inquirer/prompts";
import { wizard } from "../src/wizard.js";

const mockInput = vi.mocked(input);
const mockSelect = vi.mocked(select);

beforeEach(() => vi.clearAllMocks());

describe("wizard", () => {
  it("retorna Config com os valores respondidos", async () => {
    mockInput
      .mockResolvedValueOnce("meu-projeto")
      .mockResolvedValueOnce("./vault");
    mockSelect
      .mockResolvedValueOnce("fastapi-supabase")
      .mockResolvedValueOnce("claude");

    const config = await wizard();

    expect(config.projectName).toBe("meu-projeto");
    expect(config.stack).toBe("fastapi-supabase");
    expect(config.vaultPath).toBe("./vault");
    expect(config.agentType).toBe("claude");
    expect(config.templatesRef).toBe("latest");
  });

  it("trim no projectName", async () => {
    mockInput
      .mockResolvedValueOnce("  meu projeto  ")
      .mockResolvedValueOnce("./vault");
    mockSelect
      .mockResolvedValueOnce("nextjs-prisma")
      .mockResolvedValueOnce("cursor");

    const config = await wizard();
    expect(config.projectName).toBe("meu projeto");
  });

  it("aceita agentType none", async () => {
    mockInput
      .mockResolvedValueOnce("proj")
      .mockResolvedValueOnce("./vault");
    mockSelect
      .mockResolvedValueOnce("go-postgres")
      .mockResolvedValueOnce("none");

    const config = await wizard();
    expect(config.agentType).toBe("none");
    expect(config.stack).toBe("go-postgres");
  });
});
