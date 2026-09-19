# $0 closed-beta runbook

The 10-15-person beta uses Gemini Free Tier. Billing is not a development or launch prerequisite. Supabase remains authoritative; Drive holds explicitly requested secondary copies. Never paste real secrets into chat or commit them.

## Configuration the account owner must supply

Use a separate staging Supabase project and synthetic test accounts before inviting testers. Current local inspection found no database, Gemini, Google OAuth, Supabase public, or E2E account credentials. Existing hosted settings were not inspected, so this does not claim they are absent on Render/Vercel.

1. **Backend / Render:** set `DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_SECRET_KEY` (or legacy `SUPABASE_SERVICE_ROLE_KEY`), and a strong `TOKEN_ENCRYPTION_KEY`. Keep `DATABASE_SCHEMA_VERIFY=true`. Use the exact database project for both database and JWT verification. Use `ENVIRONMENT=staging` and `APP_ENV=staging` for staging; use `production` for the real beta service.
2. **Gemini / backend only:** set `GEMINI_API_KEY` from Google AI Studio; keep `AI_DATA_MODE=free_redacted`, `GEMINI_MODEL=gemini-2.5-flash`, `GEMINI_EMBEDDING_MODEL=gemini-embedding-001`. Google now documents authorization keys and September 2026 standard-key retirement; create a current key through AI Studio. No billing change is required by this implementation. Actual project quotas and quality must be tested.
3. **Frontend / Vercel:** set `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` (or anon key), and `NEXT_PUBLIC_API_BASE_URL=https://<your-api-host>/api/v1`. Use staging values for the staging frontend. Rebuild after changing NEXT_PUBLIC variables. The local successful build used nonfunctional build-only values, not a connected account.
4. **Google OAuth / backend:** set `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI=https://<your-web-host>/settings/integrations/google/callback`. Register that exact callback in Google Cloud. Enable Drive and Calendar APIs and add beta accounts to the consent-screen test users when applicable. The local callback is `http://localhost:3000/settings/integrations/google/callback`.
5. **Origin / MCP:** set `FRONTEND_URL` and `CORS_ORIGINS` to the selected web origin; set `MCP_ISSUER_URL` to the API origin, `MCP_RESOURCE_SERVER_URL` to `https://<your-api-host>/mcp`, and `MCP_ALLOWED_HOSTS` to the exact API host. Do not use wildcard CORS. Create separate MCP keys from Settings > AI assistant access; read-only is the default.
6. **Staging test users:** create two confirmed accounts in staging. Store `E2E_EMAIL`, `E2E_PASSWORD`, `E2E_EMAIL_B`, `E2E_PASSWORD_B` in GitHub's `beta-staging` environment secrets or the gitignored `apps/web/e2e/.env.local`. Never use real tester private records for automated tests.

Sources checked September 17, 2026: [API keys](https://ai.google.dev/gemini-api/docs/api-key), [Gemini pricing](https://ai.google.dev/gemini-api/docs/pricing), [model lifecycle](https://ai.google.dev/gemini-api/docs/deprecations), [unpaid-service data terms](https://ai.google.dev/gemini-api/terms). Redaction is not anonymization or a guarantee that identifying text cannot escape. Avoid sensitive/confidential input. Browser speech recognition can use the browser vendor's service; photo OCR runs in-browser and downloads its engine/language data on first use.

## Database and release gates

- Canonical schema is `supabase/migrations`, never SQLAlchemy `create_all` in deployment.
- Outstanding beta migrations include `20260916000024_beta_publications_and_feedback.sql`, `20260917000025_document_normalization.sql`, and `20260917000026_account_closure_and_storage.sql` for publications/feedback, document conversion metadata, and closure/Storage policies. Do not apply all historical migrations again to an existing project. Use the project's migration history and apply outstanding migrations in order after review/backup.
- For an **empty disposable staging database only**, `scripts/db/bootstrap_migrations.py` bootstraps migrations using `POSTGRES_TEST_DATABASE_URL`. Remote targets additionally require `BOOTSTRAP_ALLOW_ISOLATED=1`; populated public schemas are refused. It is not an incremental production migration tool.
- The `PostgreSQL tenant and schema gate` CI job creates pgvector PostgreSQL, bootstraps the real migration chain, and runs integration tests. `scripts/check_test_evidence.py` rejects empty/skipped results. The vector test uses explicit test embeddings; it proves database behavior, not model quality.
- Security & Quality CI runs Python lint, Bandit, unit tests, mypy, frontend lint/typecheck/unit tests/build. PostgreSQL integration runs separately.
- Configure `beta-staging` environment variables `BETA_WEB_URL`, `BETA_API_URL` (including `/api/v1`), `BETA_SUPABASE_URL`; secret `BETA_SUPABASE_PUBLISHABLE_KEY`; and the four E2E secrets above. Manually dispatch `Closed beta staging E2E`. Missing credentials fail rather than silently pass. It tests desktop/mobile browser projects and rejects skipped cases.
- Verify `/health/live` and `/health/ready`, actual Render/Vercel deployment commit SHAs, signed-in capture/reload/search/source/task flows, two-user isolation, private Storage access, Google connect/refresh/disconnect, Drive retry, Calendar create/reschedule/cancel, MCP client access/revocation, and public portfolio revoke. No new deployment was performed in this implementation run.

## Tester script and evidence

Use low-sensitivity or synthetic content first:

1. Capture a real work note; review person, organization, existing project, summary, and commitment before saving.
2. Reload and check the person/history. A commitment owed by you creates a task.
3. Ask a specific question; open the citations. When AI is unavailable, the UI labels saved excerpts rather than pretending to synthesize an answer. Ask `show overdue tasks` for a deterministic date query.
4. Connect a compatible bearer-token MCP client, retrieve the same note, then revoke its key and confirm denial. Native ChatGPT/Claude/Gemini hosted OAuth connectors remain unverified.
5. Explicitly export to your Drive or schedule one task in Calendar, then retry and check for duplicate files/events.
6. Create an evidence portfolio, save a private edit, review the exact public text, publish, open signed-out, revoke, and confirm disappearance.
7. Submit private feedback in Settings. Activity counters record captures, searches and source checks without storing query text in event metadata. These counts do not prove usefulness. Record whether the tester independently completed the loop, found accurate context, acted on a commitment, returned within seven days, and would keep using it. Obtain separate permission before publishing any testimonial.

Suggested validation targets (hypotheses, not observed traction): at least 10 activated testers; 8 complete capture-to-action unaided; 5 return within seven days; 3 separately approved testimonials. Revise targets after observing the first users. No real users, usage evidence, time savings, or testimonials have been fabricated.

## Provider upgrade later

Enabling billing does not require a code change. Keep `free_redacted` if you want minimization after billing. Only set `AI_DATA_MODE=paid_private` after verifying the provider project's paid-service terms and updating user messaging; that mode allows literal private text. Model IDs and key are configuration. Changing embedding model or privacy mode requires reindexing existing records; mixed indexes are excluded automatically. Changing the token-encryption key also changes aliases and invalidates encrypted OAuth secrets: perform a deliberate token/key rotation and reindex, not an accidental edit.

## Known beta boundaries

English photo OCR; review transcription errors. Redaction is heuristic, including limited support for unknown names in non-Latin text. No offline private-record cache or guaranteed mobile PWA installation. Voice depends on browser support/permissions. Documents support local text/Markdown/PDF/DOCX/PPTX/XLSX/CSV/JSON/HTML normalization; scanned PDFs need OCR before upload. Limits: 16,000-character captures, 24,000-character AI input, 100 chunks per record. Free quotas are unmeasured and shared; retry/error/fallback paths exist, but 15-user capacity is not certified.

Drive exports active whitelisted record fields into one Markdown archive; it is not a full attachment backup or bidirectional import. Calendar sync explicitly schedules/reschedules/cancels selected tasks; importing remote events is not implemented. Disconnect removes local OAuth tokens; users can revoke the grant in Google account settings. Portfolio links reveal exactly the reviewed text to anyone holding the link; revocation stops future access but cannot erase copies recipients made. Feedback is not testimonial consent. Structured question handling covers explicit overdue-task/open-commitment requests; broader natural language uses retrieval with evidence, not arbitrary database queries.


## Release identity and recovery proof

`GET /health` returns `release_sha` only when RELEASE_SHA or RENDER_GIT_COMMIT contains a full Git SHA. Null means the deployed revision is unverified. [Render documents its commit variable here](https://render.com/docs/environment-variables). Compare this with the tested branch SHA and the provider deployment record; a health response alone does not prove the core workflow.

The PostgreSQL CI job runs `scripts/db/verify_backup_restore.py` with `RUN_ISOLATED_RESTORE_PROOF=1`. It permits only a disposable loopback test database, creates a unique restore target, verifies data/permissions/isolation and runs the integration suite again. Both JUnit reports are retained; a skipped or failed gate is not success. Hosted Supabase Auth and Storage object recovery remain separate checks. The target server needs the roles referenced by the dump, and pg_dump/pg_restore should match the server's major version.

Private dump files, partial dumps and the default backups folder are excluded from Git. Dumps contain private data and are not encrypted by these scripts; keep them in access-controlled encrypted storage under a defined retention policy. Original attachment bytes are not included in PostgreSQL dumps.

Latest evidence: [September 19 verified release status](VERIFIED_RELEASE_SEP19.md). GitHub billing is unlocked; Security CI, 33 real PostgreSQL tests and the real restore drill pass on the recorded implementation SHA. Hosted verification remains blocked on staging access. Reproduce the earlier synthetic local document measurements with `apps/api/.venv/Scripts/python.exe scripts/benchmark_document_pipeline.py`. This does not call Gemini or measure semantic ranking.
