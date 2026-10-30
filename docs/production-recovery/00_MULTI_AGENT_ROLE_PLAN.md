# 00 — Multi-Agent Role Plan (Sequential Recovery)

**Author:** Principal Recovery Engineer / Git Release Manager  
**Date:** 2026-08-25  
**Repository:** `t4j44/mysecondbrain` (`E:\second brain`)  
**Canonical branch target:** `recovery/core-daily-driver`  
**Execution rule:** **NO parallel coding agents.** One agent, one phase, sequential handoff only.

---

## ADHD / Scope Constraint (Non-Negotiable)

- **Zero-friction capture** is sacred: capture → classify → act must stay short.
- **Do not expand scope.** No drive-by refactors, no “while we’re here” features.
- **Core Daily Driver (v0.1)** = **Venture → Project → Task + People** only.
- Explicitly **out of v0.1 product work** until later phases: Google live sync productization, portfolio/growth analytics UI, knowledge-graph UX, RAG product polish beyond Prompt 4 gates, MCP write productization beyond Prompt 5 gates.
- If a phase discovers adjacent work, **document it** — do not implement it in that phase.

---

## Why Sequential (Not Parallel)

Prior recovery work mixed automated bulk edits, quarantine moves, deleted tests, and frontend auth fixes. Parallel coding agents caused:

- Scripted replacements that can break indentation / contracts
- Unclear ownership of KEEP vs REVERT
- Premature feature work on an untrusted tree

**Rule:** Only one coding agent may mutate the tree at a time. Independent QA / Release Gate agents must use **fresh sessions** that did not build the product under review.

---

## Phase Map — Prompts 1–7 + Final Gate

| Phase | Agent Role | Prompt | Primary Deliverable | Hard Stop If | GO → Next Only If |
|-------|------------|--------|---------------------|--------------|-------------------|
| **0/1** | Principal Recovery Engineer / Git Release Manager | **Prompt 1** | Branch `recovery/core-daily-driver` + `11_LOCAL_DIFF_REVIEW.md` + structured commits | Recovery defects unfixed; verification FAIL; secrets staged; status **NOT READY** | **READY FOR CORE FRONTEND** |
| **2** | Senior Next.js Product Integration Engineer | **Prompt 2** | Ventures/Projects/Tasks/People wired + `12_CORE_DAILY_DRIVER_FRONTEND.md` | Any core domain FAIL (CRUD, auth headers, stubs remain for those four) | All four domains PASS in report |
| **3** | **Independent Senior QA (NEW SESSION)** | **Prompt 3** | Playwright auth fixtures + `13_CORE_E2E_GATE.md` | Auth fixture missing/fake; vacuous asserts; **NO-GO** | E2E gate **GO** |
| **4** | Senior AI Infrastructure / Retrieval | **Prompt 4** | Real RAG path + `14_REAL_RAG_AI_CHAT.md` | Hardcoded scores remain; simulated-only provider in “real” path; **RAG FAIL** | RAG gate PASS |
| **5** | Senior MCP / Work Intelligence | **Prompt 5** | `finalize_work_session` + `15_FINALIZE_WORK_SESSION_MCP.md` | Finalize missing/broken; write tools unsafe; **FINALIZE FAIL** | Finalize + MCP write gate PASS |
| **6** | Personal Intelligence / Evidence | **Prompt 6** | Daily memory / evidence path + `16_DAILY_MEMORY_EVIDENCE.md` | Daily memory path FAIL | Daily memory gate PASS |
| **7** | Senior Google Workspace Integration | **Prompt 7** | Live Google integration + `17_GOOGLE_WORKSPACE.md` | Critical security regression | Document **OAUTH BLOCKED** is acceptable; fake-success metrics are not |
| **8** | **Independent Principal Release Gatekeeper (NEW SESSION)** | **Final** | `V01_RELEASE_GATE.md` | Any P0 open; false “100% integrated” claims; **NO-GO** | Explicit **GO** for personal v0.1 only |

---

## Recommended Agent Roles (Ownership / I/O / Stop)

### Phase 0/1 — Principal Recovery Engineer / Git Release Manager (THIS SESSION)

| | |
|---|---|
| **Owns** | Local ↔ GitHub reconciliation; classification of every dirty file; recovery-only fixes; branch + structured commits; verification matrix |
| **Inputs** | Working tree vs `main`; `docs/production-recovery/*`; `docs/final-audit/*`; high-risk file list |
| **Outputs** | `recovery/core-daily-driver`; `00_MULTI_AGENT_ROLE_PLAN.md`; `11_LOCAL_DIFF_REVIEW.md`; commits: docs / fix / test |
| **May change** | Broken imports, invalid TS, scripted-edit mistakes, Pydantic contracts, quarantine handling, test harness, CI, fail-closed env, identified security hygiene |
| **Must not** | New product features; Google; portfolio product; RAG product; MCP writes product; UI redesign; Prompt 2 domains |
| **Stop** | Emit **NOT READY** and halt pipeline if verification fails or high-risk defects remain |
| **Handoff gate** | Status line: `READY FOR CORE FRONTEND` or `NOT READY` |

### Phase 2 — Senior Next.js Product Integration Engineer

| | |
|---|---|
| **Owns** | Wire UI for Ventures, Projects, Tasks, People against existing authenticated API |
| **Inputs** | Prompt 1 READY tree; founder/network API contracts; existing hooks/clients |
| **Outputs** | Working Core Daily Driver UI + `12_CORE_DAILY_DRIVER_FRONTEND.md` |
| **Stop** | Any of the four domains still stubs/toast-only or auth broken |
| **Must not** | Start Prompt 3; expand into RAG/Google/portfolio |

### Phase 3 — Independent Senior QA (FRESH SESSION)

| | |
|---|---|
| **Owns** | Adversarial E2E: real auth, real assertions, no builder bias |
| **Inputs** | Prompt 2 deliverable only (not builder chat history) |
| **Outputs** | `13_CORE_E2E_GATE.md` with GO/NO-GO |
| **Stop** | **NO-GO** if Playwright auth fixture fake/missing or asserts vacuous |
| **Must not** | “Fix while testing” product code beyond minimal harness bugs documented as QA findings |

### Phase 4 — Senior AI Infrastructure / Retrieval

| | |
|---|---|
| **Owns** | Replace hardcoded RAG scores / ILIKE-as-vector; fail closed when keys missing |
| **Inputs** | GO from Phase 3 (or explicit user override documented) |
| **Outputs** | `14_REAL_RAG_AI_CHAT.md` |
| **Stop** | **RAG FAIL** if confidence still hardcoded or “pass” via simulation labeled as real |

### Phase 5 — Senior MCP / Work Intelligence

| | |
|---|---|
| **Owns** | `finalize_work_session` + safe MCP write tools with authz |
| **Inputs** | Phase 4 PASS (or documented deferral) |
| **Outputs** | `15_FINALIZE_WORK_SESSION_MCP.md` |
| **Stop** | **FINALIZE FAIL** |

### Phase 6 — Personal Intelligence / Evidence

| | |
|---|---|
| **Owns** | Daily memory capture → evidence linking path for personal use |
| **Inputs** | Phase 5 PASS |
| **Outputs** | `16_DAILY_MEMORY_EVIDENCE.md` |
| **Stop** | **DAILY MEMORY FAIL** |

### Phase 7 — Senior Google Workspace Integration

| | |
|---|---|
| **Owns** | Real OAuth + real Drive/Calendar calls; honest failure modes |
| **Inputs** | Phase 6 PASS |
| **Outputs** | `17_GOOGLE_WORKSPACE.md` |
| **Stop** | Security regression; **OAUTH BLOCKED** may be documented without fake PASS metrics |

### Phase 8 — Independent Principal Release Gatekeeper (FRESH SESSION)

| | |
|---|---|
| **Owns** | Zero-trust re-verification of claims vs code vs tests |
| **Inputs** | All phase reports + current SHA on `recovery/core-daily-driver` (or release candidate branch) |
| **Outputs** | `V01_RELEASE_GATE.md` — **GO** or **NO-GO** |
| **Stop** | **NO-GO** on any open P0, simulated-as-real integrations, or dishonest status docs |
| **Must not** | Be the same session/agent that implemented Prompts 2–7 product work |

---

## GO / NO-GO Gates (Between Phases)

```
Prompt 1  --READY FOR CORE FRONTEND--> Prompt 2
Prompt 2  --all core domains PASS----> Prompt 3 (fresh QA)
Prompt 3  --E2E GO-------------------> Prompt 4
Prompt 4  --RAG PASS-----------------> Prompt 5
Prompt 5  --FINALIZE PASS------------> Prompt 6
Prompt 6  --DAILY MEMORY PASS--------> Prompt 7
Prompt 7  --honest Google status-----> Final Gate (fresh)
Final     --GO-----------------------> personal v0.1 release candidate
```

Any **NO-GO / NOT READY / FAIL** **halts** the pipeline. Later prompts must not start “to save time.”

---

## Git Release Rules (All Phases)

- Work on `recovery/core-daily-driver` (or later `recovery/*` children). **Do not push to `main`.**
- **Do not push** unless the user explicitly asks.
- No force push, no `--no-verify`, no amend except per Git Safety Protocol.
- Do not commit secrets (`.env`, credentials, keys).
- Prefer small structured commits over mixed mega-commits.

---

## Current Local Reality (Grounding for Prompt 1)

As of Prompt 1 start (2026-08-25):

- Local `main` is **1 commit ahead** of `origin/main` (`eec2e20` mypy/python 3.12 fix) — **not pushed**.
- Large dirty tree: quarantine of Agent 9 endpoints/repos, auth hook fixes, MCP/AI/portfolio schema churn, frontend shell/dashboard edits, deleted API tests, docs under `docs/final-audit/` and `docs/production-recovery/`, scratch `fix_auth.py` / `fix_imports.py`.
- Prompt 1 must **classify, fix recovery defects only, verify, commit structured** — then stop.

---

## Prompt 1 Exit Criteria (Copy Into `11_LOCAL_DIFF_REVIEW.md`)

Report:

- **BRANCH**
- **COMMIT SHA**
- **FILES CHANGED**
- **TESTS PASSED / FAILED / BLOCKED**
- **RECOVERY BRANCH STATUS:** `READY FOR CORE FRONTEND` | `NOT READY`

If **NOT READY**, Prompt 2 **must not start**.
