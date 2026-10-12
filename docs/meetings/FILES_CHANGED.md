# Meeting Intelligence V1 changed-file manifest

Branch: `feature/meeting-intelligence-v1`. HEAD: `8862f701c8a2ef12aff58bdf7613da8eb40e87ec`. Implementation is uncommitted.

55 content files plus this manifest. Hashes identify local bytes, not a commit or release SHA.

| File | Change | SHA-256 |
| --- | --- | --- |
| `.github/workflows/postgres.yml` | modified | `70814cc0f1308468baaae60b4973e917f3e7df3d3c8a0c038dac9e123295b906` |
| `.github/workflows/security_ci.yml` | modified | `37d5ced50e8831755a484854d809accabbca7728e4cb6614bd3c7262f339f2ba` |
| `apps/api/.env.example` | modified | `293e38af66a7dfb7d05d157842524964137a3b470c6b6bdd5d16f1fcf9b2dbd7` |
| `apps/api/Dockerfile` | modified | `ad7c41a4ea04cde8a7bc1f2978aa9a7b5c8446decd74b8b1aae48cc140b9fc34` |
| `apps/api/app/ai/indexing.py` | modified | `4859268471370827383b6df62f037c3922d6cf9f567df355f2e7691a236b6319` |
| `apps/api/app/ai/meeting_provider.py` | new | `7f85a168ef39acdbebd48e561c48da9b484191a68c515857bf3c09a83bb7fa4e` |
| `apps/api/app/ai/provider.py` | modified | `870b1078996ad16a3e01bc552c485d65e8bb0101260da6336f79742fe8c9a59e` |
| `apps/api/app/ai/retrieval.py` | modified | `0dd13590a3bccce44f03be182f770b210e93afb9011d4b13775a9c9162eb8b67` |
| `apps/api/app/api/v1/endpoints/meeting_intelligence.py` | new | `324b66a5f2aeb1e2c6b0b4fbcb602917be35f4a897c2fbdffa85f7af98c09b17` |
| `apps/api/app/api/v1/router.py` | modified | `1d992b54d12f19167dd46c37c9642381eebed883c1b3db18323ff2e6c01f423f` |
| `apps/api/app/config.py` | modified | `4478452883ea92d0c00563de42c89a04e5496a4da4352f8946810d43de4011b2` |
| `apps/api/app/db/schema_contract.py` | modified | `2312a940f0f892cbb60161640b377013706363bd7d398c02096947c7079c6da3` |
| `apps/api/app/jobs/handlers/meeting_processing.py` | new | `33b9bf8dd087aa6bc85cf72e875816d01ae72c48b1fe218d2eb0e114206ee2e0` |
| `apps/api/app/jobs/runner.py` | modified | `592f0afd53e41af228ec5b3e9ddc0f88626ce73787e999007594f24251dbe007` |
| `apps/api/app/models/entities.py` | modified | `814e5ab956aa3300a328a440ad8ee2c3537e32588638bd926fa8bce9cf5a067d` |
| `apps/api/app/models/meeting_intelligence.py` | new | `1862cb01102c3edc4af103aa821b2895ee03a4903049bcadc6c22ac6f15dc2f1` |
| `apps/api/app/repositories/meetings.py` | modified | `1b023a8955216b4c52a6707fa4db037f8b11136f3418683684e67728a23b873d` |
| `apps/api/app/schemas/meeting_intelligence.py` | new | `ccf9ef379b663684a3a4b4c011bcb2cfe54670d3a19ac8f686e1f420bc6d2e40` |
| `apps/api/app/schemas/meetings.py` | modified | `ecd2208697cf9d6b80ce36d12749a1275a69f8f830cca56b73d555a8af0321cd` |
| `apps/api/app/services/account.py` | modified | `3432745c86f84a9bd25eed7ff319a942dd5b2c9a10a77d948dfa5b65feafd87d` |
| `apps/api/app/services/context_events.py` | modified | `225fbfffe9ae648c81451402e2d4bdde7193f3937407402aedefe925a8a96814` |
| `apps/api/app/services/meeting_audio.py` | new | `fb4b91456dc772de90e315c28a84b0ed7b0d64557b47bc278eb2326344ae9dd0` |
| `apps/api/app/services/meeting_intelligence.py` | new | `31b6ecd2475c4c1f27aca8d2679776dcbaa06ae7c828a4447c279079fbe59588` |
| `apps/api/app/services/meeting_live.py` | new | `d7ec1c09bbad23a7d089716a0d51f3c86c63a3e18205c2e954b50aded801faec` |
| `apps/api/app/services/meeting_usage.py` | new | `2800f414d98e1c630db7bd47d5ab5db1ebe9006950f11ac2b447e7a4bccc247a` |
| `apps/api/app/services/network.py` | modified | `9af75c64b5666d3f02ee7d7a18178f5b1fed02a866a797ef8e8e0da78728f164` |
| `apps/api/pyproject.toml` | modified | `722930f2bcd2d229a44fd27aec78ecc89d3bcd8eced109c463901c9717334512` |
| `apps/api/requirements.txt` | modified | `2918cdddbc99bd97ca14bbf1ee2b541b811330792c3600e90e1ac26933cc2c7f` |
| `apps/api/scripts/meeting_provider_smoke.py` | new | `d318efef04cdb07e786d8be77ea0a2726624d63bf6de49f52fd493b406689464` |
| `apps/api/scripts/meeting_staging_storage_smoke.py` | new | `b78a97c3c0a0d416de9b16ee87283c6a64911dab42ef75d79f87bb8a28106f5d` |
| `apps/api/tests/integration/test_meeting_intelligence_postgres.py` | new | `f36163323c482f1bdba57e67558c0a072a43e9c332f307ca486a088f2bc3da72` |
| `apps/api/tests/test_account_readiness.py` | modified | `5ec7169c92cab89c1cf6808ae804c336d7e46044b6e8498f516baf925dbac5a9` |
| `apps/api/tests/test_g2_rls_security.py` | modified | `f15cf9ebb4608e0fd27339ff88895e0cf0ef197696e0c99d3c31b4263c17a0a6` |
| `apps/api/tests/test_meeting_intelligence.py` | new | `49017448be46c3f604086b896bba19191f48fbcd3c05f7a69a931a51fd1f2132` |
| `apps/api/uv.lock` | modified | `08a76d5ab539fbe56f34a57f638c12fe7ef90b3b27772cdd3357de39d6c4e90d` |
| `apps/web/__tests__/components/meeting-live.test.ts` | new | `3e75f4a0d408f936813b27b8e809aac81b77b846bb7693304f354ad5a706e9ea` |
| `apps/web/__tests__/components/meetings.test.tsx` | new | `6a651704333b2b887a4a0be09e5900b6da9c099e9505758df9b94ed165bce78a` |
| `apps/web/app/(dashboard)/meetings/[meetingId]/page.tsx` | modified | `cfe376115844e1de322c4e4043e51c9e7033cd8e3f3b2db8408c3304afa0d7dc` |
| `apps/web/app/(dashboard)/meetings/page.tsx` | modified | `34e62f62e09b2ad2457f8b4f57f582ac1394044ee0e190c790cc873a548f1431` |
| `apps/web/app/(dashboard)/settings/privacy/page.tsx` | modified | `c8f726ba322bb9e525c990e1dd3ad3c0b1919331fbe91cbd988269af4847257f` |
| `apps/web/components/meetings/capture-panel.tsx` | new | `f635263ed3257af0fa818074838fa947dbf988012cbed90656e3d63fe9c7eb5b` |
| `apps/web/hooks/useMeetings.ts` | modified | `25de268749f1f411a5b7cc28d07f03f0e47e56f54810c07c42226d53cf391bfc` |
| `apps/web/lib/meetings/api.ts` | new | `c204cdea9de5fb355bd08fbd6efae366f9fca9d3badcb67f09f626f16d1f56ce` |
| `apps/web/lib/meetings/live.ts` | new | `77d311d1c600ae14abb6400915ebd9b23c3c70bfd5f77dee67946e9604bef0f8` |
| `apps/web/lib/meetings/local-recordings.ts` | new | `d263bd2a46a4232222db8e79a1b8c59c7f39297d3895647a90bcbfca0ca25284` |
| `apps/web/lib/meetings/recorder.ts` | new | `fb7d21d24d42dc1ae1b919927338c1be3b150a444044aba7b0d84b0922da1e1f` |
| `apps/web/lib/meetings/types.ts` | new | `ac93121f5dddd668debb8fe06ce5e0433bf50bfec77a98b2083afd73452fb81f` |
| `apps/web/lib/meetings/upload.ts` | new | `23e8591c4d53b612eca63fe597c16e06b7c275da58b5001c1ea115005409fe88` |
| `apps/web/package.json` | modified | `98a90c1d9debad4afc09bbbbc2f7d6c4936b605ef947c364b0f224cbeed32894` |
| `apps/web/public/meeting-pcm-worklet.js` | new | `f5bd8e2f63a00f4a04cdfd4e7e333fc9d8aa65e8b688be1ae0638b54f1710629` |
| `apps/web/scripts/meeting-ui-smoke.fixture.tsx` | new | `a8d2c98fb9d59855b95bbd8233a487e4cfb93931f245eba5f0e0c7d390d0b421` |
| `apps/web/scripts/meeting-ui-smoke.mjs` | new | `d8b52cefb9bb30eb263e6a79cb74d45ef30d64d4a46e8b401f0dcb9bd5bfc47c` |
| `docs/meetings/HANDOFF.md` | new | `1d159b797ab315d2be4a344ecda04ba3d3214d4049f980ce48a82fe4770991d1` |
| `docs/meetings/IMPLEMENTATION_AUDIT.md` | new | `2a9485e610532d62078ccac0674b8f57a8090f3bcd3c48a0980a66573f2085b7` |
| `supabase/migrations/20261008000032_meeting_intelligence.sql` | new | `9ad8349f484e88695eb46ed9e97c79339cfe03726e28e75fc1fc334b0f84fc1b` |

Excluded: pre-existing unrelated untracked artifacts, runtime/test outputs and regenerable graph outputs.
Graphify backed up and refreshed graph.json, GRAPH_REPORT.md, graph.html, manifest and parser caches; no semantic AI extraction ran.
