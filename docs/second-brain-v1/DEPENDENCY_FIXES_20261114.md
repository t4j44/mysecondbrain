# Dependency remediation — 2026-11-14

Quality run `43598679184` successfully ran the Python 3.12 audit after #53 and reported three vulnerable locked dependencies. The gate failed and later quality checks did not run.

| Package | Before | Candidate | Primary evidence |
|---|---|---|---|
| dnspython | 2.9.0 | 2.9.2 | [Upstream 2.9.2 release](https://github.com/rthalley/dnspython/releases/tag/v2.9.2), WKS parsing resource exhaustion |
| opentelemetry-api | 1.45.1 | 1.45.2 | [Upstream advisory](https://github.com/open-telemetry/opentelemetry-python/security/advisories/GHSA-mf5v-w3w3-f6cg), traceparent parsing denial of service |
| soupsieve | 3.0.3 (2.10 on older Python patches) | 4.1 | [Upstream changelog](https://facelessuser.github.io/soupsieve/about/changelog/), selector performance and parser fixes |

Regenerated `uv.lock` and hash-pinned `requirements.lock` with targeted upgrades only. Direct dnspython floor and transitive uv constraints prevent a later resolver from selecting the reported vulnerable versions. No advisory suppression or shared-environment installation.

Compatibility: Soup Sieve 4.1 requires Python 3.11.5+, so project metadata now declares that minimum (previously 3.11). CI uses 3.12; local test interpreter is 3.11.16. Container uses the maintained 3.11 image and still needs its rebuild evidence. Soup Sieve 4 changes HTML template/iframe selector semantics; existing document conversion tests must pass against the regenerated lock. Removal of the older Python-only Soup Sieve and tomli branches is expected.

`uv lock --project apps/api --check --offline`: PASS. Full audit, backend, document conversion, frontend and container results are pending the candidate CI run. Source and lock changes alone do not establish a patched deployed service.
