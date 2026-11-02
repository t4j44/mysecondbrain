# Solo dogfood week — prep checklist (2026-11-03)

Scope: one owner, own real notes, staging only. This is NOT the 5–10-user invite beta
(see INVITE_ONLY_RELEASE_2026-11-02.md) and NOT a public or paid launch (issue #32 stays NO-GO).

Verified 2026-11-03: `main` a8f3880 — Security & Quality CI and PostgreSQL gate both green.

## Prep (owner actions need dashboards/secrets; do not paste values into chat or git)

- [ ] 1. Rotate the staging Supabase database password (Supabase dashboard > Database settings).
      Update Render's DATABASE_URL, redeploy, confirm `/health/ready` = 200 and you can still sign in.
- [ ] 2. Backup before real data goes in. On your machine with `pg_dump` 17 installed:
      `DATABASE_URL=<session-pooler url> python scripts/backup/backup.py`
      then restore into a throwaway local Postgres with `scripts/restore/restore.py` and compare row counts.
      Storage object bytes are NOT in the dump. Repeat weekly (the Free plan has no managed backups).
- [ ] 3. Put current `main` on the staging web alias. `apps/web/vercel.json` skips `main` builds; use the
      protected preview branch flow from docs/v2/FULL_EXPERIENCE_RECOVERY_2026-11-02.md, then confirm
      the alias serves the new build (`/privacy` should load without redirecting to login).
- [ ] 4. Create synthetic users A and B, add E2E_EMAIL / E2E_PASSWORD / E2E_EMAIL_B / E2E_PASSWORD_B to the
      GitHub `beta-staging` environment secrets, run the "Closed beta staging E2E" workflow, keep the receipt.
- [ ] 5. Keep Telegram, Google sync, public portfolio and billing OFF.

## Rules for the week

- Only data you can afford to lose. No confidential client or third-party sensitive data.
- Daily 2-minute check: backend `/health/ready`, any error you saw, anything that lost or mangled data.
- Log one line per use in the table below.

| Date | What I did | What broke or confused me | Would I pay for this? |
|---|---|---|---|

## Exit criteria for inviting others

Zero data loss, zero cross-user exposure, you used it unprompted on most days, and the P0 gates in
INVITE_ONLY_RELEASE_2026-11-02.md pass (privacy/terms sign-off, Supabase signups disabled in the dashboard).
