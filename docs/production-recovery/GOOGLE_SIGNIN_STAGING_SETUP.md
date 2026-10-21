# Google sign-in activation — Second Brain staging

The frontend Google button is already implemented. It only enables itself when
the managed Supabase Auth `/auth/v1/settings` endpoint advertises `external.google=true`.
No Google client secret belongs in GitHub, Vercel, frontend variables or chat.

## One-time provider configuration

1. In Google Auth Platform (Google Cloud Console), configure the OAuth consent screen for testing.
   Use a **Web application** OAuth client with a separate **staging** client ID/secret.
   Add the operator's Google account as a test user if the consent screen is in Testing mode.
2. Authorized JavaScript origin:
   `https://second-brain-web-staging-seven.vercel.app`
3. Authorized redirect URI (Google -> Supabase, **not** the Next.js callback):
   `https://rpkjmdrralzxhdsgceal.supabase.co/auth/v1/callback`
4. Supabase project `second-brain-staging` -> Authentication -> Sign In / Providers -> Google:
   enable Google and save the **Client ID** and **Client Secret** directly in Supabase.
5. Supabase -> Authentication -> URL Configuration: site URL
   `https://second-brain-web-staging-seven.vercel.app` and allow
   `https://second-brain-web-staging-seven.vercel.app/callback` (including its
   `next` query argument as permitted by the redirect-URL pattern).
   Use a narrow staging-host pattern; do not allow arbitrary origins or `**`.
6. Reload login/signup. The Google button checks the live provider settings.
   Click, consent with a staging Google account, return to `/callback`,
   confirm a valid Supabase session and then test dashboard and logout.

## Acceptance

- Google sign-in and signup both establish a hosted session.
- Redirect to `/dashboard` stays on Second Brain; hostile `next` values fall back safely.
- Signup or OAuth identity produces exactly one owner-scoped user profile.
- Authenticated user A cannot read/update user B's contacts, documents or meetings.
- Session refresh, logout and re-login succeed.
- Google **sign-in alone** grants no Drive, Gmail or Calendar data permissions:
  separate explicit integrations and consent are required.

If Google credentials are absent/disabled, the button remains disabled and
email/password continues working. Do not claim Google OAuth is tested based
on HTTP shell smoke tests or database fixtures.
