/**
 * doremi companion CLI
 *
 * Commands:
 * - project:focus --prefer Windsurf --alt "Code - OSS,code,Code" --project /path
 * - ide:hotkey --keys "ctrl+shift+m"
 */
import { focusProject } from "./actions/focusProject.js";
import { sendHotkey } from "./actions/hotkey.js";

/**
 * Parse a comma-or-space list into string[]
 */
function parseList(v?: string): string[] {
  if (!v) return [];
  return v.split(",").map((s) => s.trim()).filter(Boolean);
}

function getArg(name: string): string | undefined {
  const i = process.argv.indexOf(name);
  return i > -1 ? process.argv[i + 1] : undefined;
}

/**
 * Dispatch a subcommand from argv.
 * @param argv - process.argv array
 */
function dispatch(argv: string[]): number {
  const cmd = argv[2];
  switch (cmd) {
    case "project:focus": {
      const prefer = parseList(getArg("--prefer")) || [];
      const alt = parseList(getArg("--alt")) || [];
      const projectHint = getArg("--project") || undefined;
      return focusProject({ prefer, alt, projectHint });
    }
    case "ide:hotkey": {
      const keys = getArg("--keys");
      if (!keys) {
        console.error("Missing --keys");
        return 2;
      }
      return sendHotkey(keys);
    }
    default:
      console.error(`Unknown command: ${cmd}`);
      console.error("Usage: project:focus | ide:hotkey");
      return 2;
  }
}

process.exit(dispatch(process.argv));
