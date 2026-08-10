import { z } from 'zod';

/**
 * Runtime Environment Variable Validation
 * Enforces strict boundary separation between client (NEXT_PUBLIC_) and server secrets.
 */
const envSchema = z.object({
  NEXT_PUBLIC_SUPABASE_URL: z.string().url().default('https://mock.supabase.co'),
  NEXT_PUBLIC_SUPABASE_ANON_KEY: z.string().min(1).default('mock-anon-key-placeholder'),
  NEXT_PUBLIC_API_BASE_URL: z.string().url().default('https://api.tajssecondbrain.ai/api/v1'),
  SUPABASE_SERVICE_ROLE_KEY: z.string().optional(),
});

const processEnv = {
  NEXT_PUBLIC_SUPABASE_URL: process.env.NEXT_PUBLIC_SUPABASE_URL,
  NEXT_PUBLIC_SUPABASE_ANON_KEY: process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY,
  NEXT_PUBLIC_API_BASE_URL: process.env.NEXT_PUBLIC_API_BASE_URL,
  SUPABASE_SERVICE_ROLE_KEY: process.env.SUPABASE_SERVICE_ROLE_KEY,
};

const parsed = envSchema.safeParse(processEnv);

if (!parsed.success) {
  console.error('❌ Invalid runtime environment configuration:', parsed.error.format());
  throw new Error('Invalid runtime environment configuration. Check your .env setup against apps/web/.env.example.');
}

export const env = parsed.data;

/**
 * Verify server secret access attempt
 */
export function getServiceRoleKey(): string | undefined {
  if (typeof window !== 'undefined') {
    throw new Error('🚨 SECURITY ALERT: Attempted to access SUPABASE_SERVICE_ROLE_KEY in a browser runtime environment.');
  }
  return env.SUPABASE_SERVICE_ROLE_KEY;
}
