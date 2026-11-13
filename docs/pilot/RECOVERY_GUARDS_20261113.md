# Recovery guard review — 2026-11-13

Base: recovery draft #46, `b2e9ed0f39dea375f9d38d63e7b406e032b2f098`. This follow-up is code hardening, not a completed staging recovery.

## Confirmed and corrected

1. Windows directory setup removed inherited access but retained other explicit Allow entries. New directories receive a fresh owner-only protected DACL; existing directories must pass owner/inheritance/explicit-access checks or fail closed. No existing directory permissions are silently rewritten. The built-in Windows PowerShell security module is loaded explicitly when invoked from a PowerShell 7/Python environment.
2. Export read the full dump before enforcing size limits. Dump and manifest sizes are now checked first; the dump streams into the archive, metadata serialization is bounded, and restore enforces matching per-member caps before writing plaintext.
3. A connection-close failure skipped dump deletion. Cleanup now runs in `finally` with a bounded close and propagates deletion failures.
4. Coroutine cancellation could abandon a still-running dump thread. The export now waits for its shielded worker, removes the returned plaintext and then propagates cancellation, keeping the snapshot alive until the dump ends.
5. Restore loaded an oversized encrypted file before checking its envelope limit. A bounded reader checks size and read length; the checksum refers to the exact envelope decrypted.

## Observed evidence

`python -m unittest discover -s scripts/backup/tests -p test_private_recovery.py -v`: **20 PASS, 0 skipped on Windows**. Includes real Windows DACL creation/reuse and explicit Everyone-read rejection on a disposable synthetic directory, thread cancellation cleanup, close/unlink failure handling, oversize prechecks/file growth, authenticated encryption/tampering, archive traversal/link rejection and comparison drift checks.

An independent source reviewer reproduced the reasoning for the first three defects and confirmed their fixes, then identified the cancellation and restore-input gaps. Final re-review of those follow-ups is recorded in the PR. No private credentials or customer data were used in tests.

## Unverified release gates

- Real staging DB/Auth-data export, encrypted owner-private Drive copy, downloaded checksum and independent PG17+pgvector restore: NOT RUN.
- Local manifest comparisons do not establish managed Auth service configuration, Storage object-byte recovery, full schema-object coverage, or actual two-user RLS behavior. Inventory views/sequences/types and provider extension compatibility before claiming full recovery.
- Process termination/power loss and SSD secure erasure cannot be guaranteed by Python cleanup. Plaintext work directories must remain owner-private; encryption-key recovery must be documented outside Drive/repository.
- Existing real private setup was unavailable at the last non-secret check. No credential was decrypted, rotated, printed or copied by this patch.
- No hosted migration, deployment, public link, invitation or production change. Git deployment is disabled for this review branch. Revert this follow-up commit to restore the base tooling; do not use that older tooling for real data until the confirmed defects are addressed.
