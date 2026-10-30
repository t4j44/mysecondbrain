# Isolated staging dependency security refresh (candidate)

This is an unmerged security branch. It is not proof of production readiness.

The locked Python dependency audit reported nine issues across:
- certifi 2026.7.22 -> candidate 2026.10.19 (PYSEC-2026-4320)
- Pillow 12.3.0 -> candidate 13.0.0 (8 CVE findings)

The isolated GitHub Actions uv job regenerated **both** `apps/api/uv.lock`
and hashed `apps/api/requirements.lock` from the updated
`apps/api/pyproject.toml`; it did not modify production resources.

Acceptance still required:
- `pip install --require-hashes -r apps/api/requirements.lock`
- `pip-audit --require-hashes` with zero reported vulnerabilities
- full backend unit tests, Bandit/Ruff/mypy
- full PostgreSQL fresh/upgrade/restore and Docker startup
- frontend production build and browser-component tests
- staging-only deploy and real document/image extraction regression

Until all checks pass, this branch remains draft and is not promoted.
