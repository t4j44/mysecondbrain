import { z } from 'zod';

/**
 * Runtime Environment Variable Validation
 * Enforces strict boundary separation between client (NEXT_PUBLIC_) and server secrets.
 */
const envSchema = z
  .object({
    NEXT_PUBLIC_SUPABASE_URL: z.string().url(),
    NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY: z.string().min(1).optional(),
    NEXT_PUBLIC_SUPABASE_ANON_KEY: z.string().min(1).optional(),
    NEXT_PUBLIC_API_BASE_URL: z.string().url(),
    SUPABASE_SECRET_KEY: z.string().optional(),
    SUPABASE_SERVICE_ROLE_KEY: z.string().optional(),
  })
  .refine(
    (data) =>
      Boolean(data.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY || data.NEXT_PUBLIC_SUPABASE_ANON_KEY),
    {
      message:
        'Provide NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY or NEXT_PUBLIC_SUPABASE_ANON_KEY',
      path: ['NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY'],
    }
  )
  .transform((data) => {
    const publishableKey =
      data.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY ||
      data.NEXT_PUBLIC_SUPABASE_ANON_KEY!;
    return {
      ...data,
      NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY: publishableKey,
      NEXT_PUBLIC_SUPABASE_ANON_KEY: publishableKey,
    };
  });

const processEnv = {
  NEXT_PUBLIC_SUPABASE_URL: process.env.NEXT_PUBLIC_SUPABASE_URL,
  NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY: process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY,
  NEXT_PUBLIC_SUPABASE_ANON_KEY: process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY,
  NEXT_PUBLIC_API_BASE_URL: process.env.NEXT_PUBLIC_API_BASE_URL,
  SUPABASE_SECRET_KEY: process.env.SUPABASE_SECRET_KEY,
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
export function getSecretKey(): string | undefined {
  if (typeof window !== 'undefined') {
    throw new Error('🚨 SECURITY ALERT: Attempted to access server secret key in a browser runtime environment.');
  }
  return env.SUPABASE_SECRET_KEY || env.SUPABASE_SERVICE_ROLE_KEY;
}

export function getServiceRoleKey(): string | undefined {
  return getSecretKey();
}
