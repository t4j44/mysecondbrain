# V1 evidence index

All screenshots in this directory use fictional/local fixture data. They show actual browser output from the changed source, not an authenticated hosted deployment.

- `home-chromium-390-synthetic.png`: global Capture/Search, five primary destinations, light tokens, empty/onboarding state.
- `meetings-chromium-320-synthetic.png`: smallest supported width, primary meeting action, filter wrapping and navigation.
- `calendar-chromium-390-synthetic.png`: actual production Schedule component with a synthetic preview, two local dates and manual download. Captured by `meeting-ui-smoke.mjs`; no hosted session or calendar-app import implied.

Commands and exact results are recorded in `../WORK_LOG.md`. Real signed-in staging screenshots must be separately labeled with deployment URL, source SHA and capture time. Do not put private content, authentication state, signed URLs or credentials here.

2026-11-16 founder-facing correction: `home-desktop-20261116-synthetic.png`, `meetings-desktop-20261116-synthetic.png`, and `home-mobile-20261116-synthetic.png` show the connected production shell/components with fictional local data. These supersede older Home onboarding imagery for this candidate. See `../VISIBLE_PRODUCT_STATUS_20261116.md` for the actual founder URL and delivery mismatch.
