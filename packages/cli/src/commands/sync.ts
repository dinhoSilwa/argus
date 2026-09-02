// ARGUS-013: implementar sync de templates com comparação de hash
export async function sync(options: { ref?: string }): Promise<void> {
  const ref = options.ref ?? "latest";
  console.log(`[TODO] argus sync --ref ${ref} — implementar em ARGUS-013`);
}
