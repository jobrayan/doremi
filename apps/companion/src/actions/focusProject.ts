/**
 * Brings your project window to front:
 * 1) Try preferred names (e.g., Windsurf)
 * 2) Fallback to alt list (e.g., VS Code class names)
 * 3) Optionally match window title containing a project path hint
 */
import { spawnSync } from "child_process";

type FocusArgs = {
  prefer: string[];     // e.g., ["Windsurf"]
  alt: string[];        // e.g., ["Code - OSS", "code", "Code"]
  projectHint?: string; // e.g., "/home/you/dev"
};

/**
 * Activate first matching window by name/class/title.
 *
 * @param args FocusArgs
 * @returns exit code (0 ok)
 */
export function focusProject(args: FocusArgs): number {
  // List windows: wmctrl -lx
  const list = spawnSync("wmctrl", ["-lx"], { encoding: "utf8" });
  if (list.status !== 0) return list.status ?? 1;

  const rows: string[] = (list.stdout || "").split("\n").filter(Boolean);

  const findMatch = (keys: string[]) =>
    rows.find((line: string) => keys.some((k) => line.toLowerCase().includes(k.toLowerCase())));

  const tryKeys: string[][] = [];
  if (args.prefer?.length) tryKeys.push(args.prefer);
  if (args.alt?.length) tryKeys.push(args.alt);

  let chosen = "";
  for (const keys of tryKeys) {
    const hit = findMatch(keys);
    if (hit) {
      chosen = hit;
      break;
    }
  }

  if (!chosen && args.projectHint) {
    chosen = rows.find((r: string) => r.includes(args.projectHint!)) ?? "";
  }
  if (!chosen) {
    console.error("No window match for focus.");
    return 2;
  }

  const wid = chosen.split(/\s+/)[0]; // window id
  const act = spawnSync("wmctrl", ["-ia", wid], { stdio: "inherit" });
  return act.status ?? 1;
}
