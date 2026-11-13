# Free-Pilot Backup and Disaster-Recovery Runbook
## Why
Code is recoverable from Git; user conversations, relationships, audio/transcripts, commitments and edits are not. Backup exists to recover **data** after deletion, schema bugs or failed changes. This does **not** mean Second Brain normally runs on the founder's PC.

## 1. Planned operating model
- **Primary database:** Supabase Cloud (never switch live traffic to Windows).
- **Backup execution:** existing staging backup/export scripts, temporarily running wherever authorized `pg_dump` and encryption tools exist. Local runtime is an **ephemeral backup tool**, not permanent hosting.
- **Off-device copy:** private, owner-only **Google Drive** folder, only authenticated encrypted backup files, separate from marketing/pilot evidence.
- **Key:** backup passphrase held in an independent password manager, not Google Drive or Git. Windows DPAPI file is a convenience for local runs, **not sufficient off-device recovery of the key**.
- **Restore target:** temporary isolated PostgreSQL 17 + pgvector environment, destroy/restrict after test. Do not create billable test branches without founder approval.
- **Long-term after funding:** approved managed encrypted offsite backups with recovery point objectives, automated drills and separate Auth/Storage recovery.

## 2. Existing work to reuse
- Main repo `scripts/backup/backup.py`: performs custom `pg_dump` + `pg_restore --list` validation; **does not copy Storage object bytes**.
- Draft PR #46, status as of 2026-11-12: private setup in `scripts/backup/private_recovery_input.ps1`, encrypted export / staging manifest, isolated PG17+pgvector restore scripts, Windows synthetic tests. **Synthetic PASS is not a real staging backup or recovery PASS.**
- Do not discard or repeatedly rebuild the form. If private setup fails, read non-secret stage/error metadata and fix the *confirmed* cause once before requesting another input. Never ask the owner to paste secrets in a coding-agent chat.

## 3. Single-pass procedure for coding agent
**Phase A — preflight**
1. Check staging project ref exact: `rpkjmdrralzxhdsgceal`. Production/legacy project may have a different ref and an older exposed credential; do not touch them.
2. Confirm staging server reachable and current password rotation operationally verified. Check private setup file existence and read-back **without printing values**.
3. Confirm Google Drive destination owner-private, sync works AND service side can list/get uploaded bytes. A `G:\My Drive` folder alone does not prove remote sync.
4. Confirm Postgres client/server/pgvector compatibility, TLS verification, output size/time boundaries and no paid resources.
5. Avoid using a database superuser for scheduling production backups long-term. Existing export role may be privileged; use strictly scoped access and short-lived credentials where practical.

**Phase B — immutable encrypted backup**
1. Execute **read-only** consistent-snapshot export of the **staging** Postgres schema and relevant data including Auth SQL records, grants/RLS as far as dump allows. Record source timestamp, version, migrations and source size; avoid logging PII.
2. Encrypt before leaving private work directory with authenticated encryption such as AES-256-GCM and a properly derived key. Document algorithm/version and restore requirements.
3. Validate encrypted envelope and local roundtrip; store source dump only temporarily, private ACLs, delete temporary plaintext as safely as applicable.
4. Upload only `.enc` to private Drive. Confirm cloud object exists with expected byte length and SHA-256. **Download cloud bytes back** and checksum; do not trust mere 'Synced' icon.
5. Keep multiple snapshots and a retention schedule (initial pilot suggestion: daily and before each risky migration, last 7 daily + 4 weekly, subject to quota). This is a proposed policy, not currently running.

**Phase C — isolated restore proof**
1. Create a **new empty** localhost-only, temporary Postgres 17+pgvector cluster (or a cloud ephemeral environment explicitly approved). Never accept a URL of staging/production as restore destination.
2. Read the **downloaded encrypted Drive copy**, decrypt in a private temporary location and restore complete required schemas/data, owner/grants/policies/functions/extensions/constraints/indexes.
3. Compare captured manifest against restored schema, row counts, digests, extensions, Auth SQL records and RLS behavior. Run synthetic login/tenant tests after restore where Auth setup permits.
4. Inventory Supabase-specific managed-service gaps: Auth provider settings/secrets, Supabase Storage **object bytes**, edge functions, provider keys, Auth recovery integration and bucket policy. SQL table rows alone are NOT full managed-Supabase recovery.
5. Log PASS/FAIL for encrypted file integrity, off-device retrieval, independent restore, Auth recovery scope, Storage bytes and data-integrity checks. Destroy temporary cluster/plaintext after validation, retaining only sanitized report.

## 4. What stays unverified if not run
- Creating form, entering password or running encryption against synthetic content is **not** a backup.
- `pg_restore --list` proves archive readability, **not** a working restored database.
- A screenshot of `G:\My Drive\SecondBrainBackups` is **not** proof Google Drive cloud sync completed.
- A restored Postgres SQL dump may not recreate hosted Supabase Auth OAuth configuration, object storage files or platform-managed secrets. Do not mark **complete** disaster recovery PASS without this scope.

## 5. Operational readiness for beta
- One tested restore from off-device bytes before inviting 5–10 users with real valued data.
- Document expected recovery point (if daily snapshot, can lose up to ~24h of changes) and recovery time from an actual test. No invented SLA.
- Backup success/failure ownership assigned; alerts or explicit daily check for manual pilot, and periodic restore rehearsals.
- Support deletion/export policy: backup retention means user deletion may remain within encrypted snapshots until snapshot expiry; disclose clearly.
- Watch Storage object count/bytes. As of earlier staging read-only checks, buckets existed but objects were zero; **recheck before making the current claim**.
- Avoid GitHub Actions artifacts for real dumps, plaintext manifests, private API logs, files, Auth sessions or passphrases.

## 6. If blocked on the private form
The coding agent must print **one non-secret status** and a single specific owner action: missing file? duplicate password field? wrong project ref? corrupt Windows DPAPI receipt? cloud Drive permission? Debug with synthetic data first. No repeated vague `Have you saved?` loops; do not require the owner to install big developer toolchains unnecessarily.
