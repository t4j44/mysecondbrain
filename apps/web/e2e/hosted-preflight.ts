import { previewCredential, tokenProvider, VERIFIED_PREVIEW_ORIGIN } from './helpers/preview-access';

// Runs before any fixture/API write. A protection page must not lead to a
// partial acceptance run that has already created staging records.
export default async function hostedPreflight() {
  const env = process.env;
  if (env.NEXT_PUBLIC_API_BASE_URL !== 'https://second-brain-api-staging.onrender.com/api/v1'
      || env.NEXT_PUBLIC_SUPABASE_URL !== 'https://rpkjmdrralzxhdsgceal.supabase.co'
      || !env.E2E_EMAIL || !env.E2E_EMAIL_B || !env.E2E_PASSWORD || !env.E2E_PASSWORD_B
      || env.E2E_EMAIL.trim().toLowerCase() === env.E2E_EMAIL_B.trim().toLowerCase()) {
    throw new Error('Hosted acceptance requires pinned staging services and two distinct synthetic accounts.');
  }
  const credential = previewCredential();
  if (process.env.PLAYWRIGHT_TEST_BASE_URL !== VERIFIED_PREVIEW_ORIGIN || !credential) {
    throw new Error('Hosted acceptance requires the pinned protected preview and short-lived identity.');
  }
  try {
    const response = await fetch(VERIFIED_PREVIEW_ORIGIN + '/login', {
      redirect: 'error', signal: AbortSignal.timeout(60_000),
      headers: { 'x-vercel-trusted-oidc-idp-token': await tokenProvider(process.env)() },
    });
    if (!response.ok) throw new Error();
    const body = await response.text();
    if (!body.includes('Sign in') || !body.includes('password')) throw new Error();
  } catch {
    throw new Error('Protected application login preflight failed; no hosted tests were started.');
  }
}
