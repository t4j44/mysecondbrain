# Signed-in UI recovery report — November 3, 2026

Branch: `recovery/exact-codex-signed-in-ui-20261102`. Base: `main` `a8f3880`. This change adds documentation and screenshots only; no application code was changed.

## Result
No original signed-in UI exists outside `main` that is missing from it. Nothing was invented or re-designed.

## Where the search looked
All local and remote branches, both Codex worktrees, the stash, the reflog and unreachable commits.
Only the following carry UI changes not reachable from `main`:

| Source | Finding |
| --- | --- |
| `design/second-brain-mobile-clarity-20261024` (PR #13, 8 files) | Shell, bottom bar, top bar, People, Work and PageHeader are already in `main` (People, Work and PageHeader are byte-identical). Home and nav differ because `main` evolved them on purpose ("Today", "More" tab, header Ask shortcut). |
| Same branch, Capture page | `main` is newer: it has the four entry cards (Record meeting, Save a person, Quick note / voice, Document / photo). Applying PR #13 would remove them. |
| `feature/visual-meetings-pilot-20261025` | `main`'s Meetings page is newer: it keeps the `?capture=1` deep link and never disposes the recorder when hidden. Applying it would regress both. |
| Stash `stash@{0}` | Backend model edits only. |
| Codex worktrees | No signed-in UI work. |

Not recoverable: any design that was never committed (for example only in a Codex task or another machine). The Codex session transcripts under `~/.codex/sessions` were not searched.

## Verification (clean `pnpm install --frozen-lockfile` in an isolated worktree)
- `tsc --noEmit`: pass.
- `next lint`: no warnings or errors.
- `next build`: pass, with synthetic public URLs as in CI. No credentials used.
- `vitest run`: 27 files, 120 tests passed.
- Screenshots: from the synthetic fixture (`apps/web/scripts/mobile-ui-server.mjs`), which uses production components with synthetic auth and API adapters and a fictional "Demo" user. This is not hosted E2E evidence and no real integrations are involved.
- Not run: Playwright E2E, which needs the four synthetic-account secrets in CI.
- Note: an existing checkout whose installed `zod` / `@hookform/resolvers` are older than `package.json` shows a spurious TS error in the login page; a fresh install does not.

## Screenshots (`docs/v2/recovery-screenshots/`)
Desktop 1440x900 and mobile 390x844: dashboard, people, capture, meetings, assistant, work.
Public production is not promoted, and the release hold (#32) is unchanged.
