/**
 * Emits a global hotkey like ctrl+shift+m via xdotool.
 *
 * @param keys e.g. "ctrl+shift+m"
 * @returns exit code
 */
import { spawnSync } from "child_process";

export function sendHotkey(keys: string): number {
  const res = spawnSync("xdotool", ["key", keys], { stdio: "inherit" });
  return res.status ?? 1;
}
