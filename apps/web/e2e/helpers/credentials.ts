import fs from 'fs';
import path from 'path';

function parseEnvFile(filePath: string): void {
  if (!fs.existsSync(filePath)) return;
  const text = fs.readFileSync(filePath, 'utf8');
  for (const rawLine of text.split(/\r?\n/)) {
    const line = rawLine.trim();
    if (!line || line.startsWith('#')) continue;
    const eq = line.indexOf('=');
    if (eq <= 0) continue;
    const key = line.slice(0, eq).trim();
    let value = line.slice(eq + 1).trim();
    if (
      (value.startsWith('"') && value.endsWith('"')) ||
      (value.startsWith("'") && value.endsWith("'"))
    ) {
      value = value.slice(1, -1);
    }
    if (process.env[key] === undefined || process.env[key] === '') {
      process.env[key] = value;
    }
  }
}

parseEnvFile(path.resolve(__dirname, '..', '.env.local'));
parseEnvFile(path.resolve(__dirname, '..', '..', '.env.local'));

export type E2EUser = { email: string; password: string };

export function getPrimaryE2EUser(): E2EUser | null {
  const email = process.env.E2E_EMAIL?.trim();
  const password = process.env.E2E_PASSWORD;
  if (!email || !password) return null;
  return { email, password };
}

export function getSecondaryE2EUser(): E2EUser | null {
  const email = process.env.E2E_EMAIL_B?.trim();
  const password = process.env.E2E_PASSWORD_B;
  if (!email || !password) return null;
  return { email, password };
}

export const AUTH_STATE_PATH = path.resolve(__dirname, '..', '.auth', 'user.json');
export const AUTH_STATE_B_PATH = path.resolve(__dirname, '..', '.auth', 'user-b.json');

export function hasSupabasePublicConfig(): boolean {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL?.trim();
  const key =
    process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY?.trim() ||
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY?.trim();
  return Boolean(url && key);
}
