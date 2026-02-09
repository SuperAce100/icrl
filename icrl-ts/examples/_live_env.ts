import * as fs from "node:fs";
import * as path from "node:path";

function parseDotEnv(text: string): Record<string, string> {
  const vars: Record<string, string> = {};

  for (const rawLine of text.split(/\r?\n/)) {
    const line = rawLine.trim();
    if (!line || line.startsWith("#")) continue;

    const idx = line.indexOf("=");
    if (idx <= 0) continue;

    const key = line.slice(0, idx).trim();
    let value = line.slice(idx + 1).trim();

    if (
      (value.startsWith('"') && value.endsWith('"')) ||
      (value.startsWith("'") && value.endsWith("'"))
    ) {
      value = value.slice(1, -1);
    }

    vars[key] = value;
  }

  return vars;
}

export function loadWorkspaceEnv(): void {
  const rootDir = path.resolve(__dirname, "..", "..");
  const envPath = path.join(rootDir, ".env");

  if (!fs.existsSync(envPath)) return;

  const parsed = parseDotEnv(fs.readFileSync(envPath, "utf-8"));
  for (const [key, value] of Object.entries(parsed)) {
    if (!process.env[key]) {
      process.env[key] = value;
    }
  }

  if (!process.env.GOOGLE_APPLICATION_CREDENTIALS) {
    const defaultCreds = path.join(rootDir, "credentials.json");
    if (fs.existsSync(defaultCreds)) {
      process.env.GOOGLE_APPLICATION_CREDENTIALS = defaultCreds;
    }
  }
}
