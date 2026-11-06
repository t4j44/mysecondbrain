# Pilot recovery execution — 2026-11-07

Policy: deep planning; inspect existing backup/restore dependencies; verify against actual isolated restore; no delegation. No new paid infrastructure, production launch or live-database restore.

Read-only staging baseline: PostgreSQL 17.11; five Auth users, eight commitments, zero Storage objects. These are aggregate counts, not identity or synthetic-user acceptance. Existing main contains the V2 release; this chat's previous branch was stale. Work is isolated from the user's dirty `E:\second brain` checkout, whose untracked backup helpers were inspected and preserved.

The local encryption helper is reused with AES-256-GCM and scrypt, stronger passphrase minimum, authenticated decryption before plaintext output and refusal to overwrite backups. A masked local form accepts the staging session-pooler URL and a passphrase; Windows DPAPI protects its local copy, which is excluded from Git. The owner must separately retain that passphrase outside Drive for recovery after loss of this Windows account.

Private Drive recovery folder created and permission metadata verified: owner-only and shared=false. No database backup has been uploaded yet. Folder is separate from pilot evidence.

Installed PostgreSQL server is 17.11. Its vector extension is missing. A branch-only standard Windows CI job builds official pgvector 0.8.2 at pinned source cab9da72c04353f143bb06b42ab70a403daac64a. It handles public source/binaries only, never staging data or secrets. No confidential data will be placed in GitHub artifacts.

Recovery status: NOT_RUN. Export credential entry and an independent restored-data comparison are still required. An encryption round trip or pg_restore --list alone is not a recovery PASS.
