# Dependency remediation — 2026-11-14

Quality run `43598679184` successfully ran the Python 3.12 audit after #53 and reported three vulnerable locked dependencies. The gate failed and later quality checks did not run.

| Package | Before | Candidate | Primary evidence |
|---|---|---|---|
| dnspython | 2.9.0 | 2.9.2 | [Upstream 2.9.2 release](https://github.com/rthalley/dnspython/releases/tag/v2.9.2), WKS parsing resource exhaustion |
| opentelemetry-api | 1.45.1 | 1.45.2 | [Upstream advisory](https://github.com/open-telemetry/opentelemetry-python/security/advisories/GHSA-mf5v-w3w3-f6cg), traceparent parsing denial of service |
| soupsieve | 3.0.3 (2.10 on older Python patches) | 4.1 | [Upstream changelog](https://facelessuser.github.io/soupsieve/about/changelog/), selector performance and parser fixes |

Regenerated `uv.lock` and hash-pinned `requirements.lock` with targeted upgrades only. Direct dnspython floor and transitive uv constraints prevent a later resolver from selecting the reported vulnerable versions. No advisory suppression or shared-environment installation.

Compatibility: Soup Sieve 4.1 requires Python 3.11.5+, so project metadata now declares that minimum (previously 3.11). CI uses 3.12; local test interpreter is 3.11.16. Container uses the maintained 3.11 image and still needs its rebuild evidence. Soup Sieve 4 changes HTML template/iframe selector semantics; existing document conversion tests must pass against the regenerated lock. Removal of the older Python-only Soup Sieve and tomli branches is expected.

`uv lock --project apps/api --check --offline`: PASS. At candidate `f5250ceb64f544c59644df708f5c6af97fc69e88`, [quality run 43622850094](https://github.com/t4j44/mysecondbrain/actions/runs/43622850094) passed hash-pinned installation, Ruff, the Python dependency audit and Bandit. Backend: **631 PASS, 1 FAIL**; document normalization passed. The failing Telegram snooze test mixes a fixed November 3 callback clock with the canonical action's wall clock; frontend checks/build were skipped. This is still a failed quality run, not a full PASS.

[PostgreSQL run 43622885461](https://github.com/t4j44/mysecondbrain/actions/runs/43622885461) passed both PostgreSQL 16 and 17, including integration evidence checks, seeded upgrade, disposable backup/restore, the actual API image build and container runtime with the updated lock. This is synthetic restore evidence, not restoration of the user's staging database. No patched service has been deployed.
