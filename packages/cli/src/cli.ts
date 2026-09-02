#!/usr/bin/env node
import { Command } from "commander";
import { init } from "./commands/init.js";
import { add } from "./commands/add.js";
import { sync } from "./commands/sync.js";

const program = new Command();

program
  .name("argus")
  .description("Instala um sistema de engenharia completo em qualquer projeto")
  .version("0.1.0");

program
  .command("init")
  .description("Configura um novo projeto com Argus")
  .action(init);

program
  .command("add <type> <name>")
  .description("Adiciona um recurso ao projeto (ex: argus add skill lint-fix)")
  .action(add);

program
  .command("sync")
  .description("Atualiza templates para a versão mais recente")
  .option("--ref <ref>", "Tag ou branch do argus-templates")
  .action(sync);

program.parse();
