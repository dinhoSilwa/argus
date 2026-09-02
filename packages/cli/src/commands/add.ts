// ARGUS-013: implementar download e cópia de skill avulsa
export async function add(type: string, name: string): Promise<void> {
  if (type !== "skill") {
    console.error(`Tipo desconhecido: ${type}. Use: argus add skill <nome>`);
    process.exit(1);
  }
  console.log(`[TODO] argus add skill ${name} — implementar em ARGUS-013`);
}
