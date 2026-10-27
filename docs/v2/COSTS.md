# Cost evidence and controls

Status: **NOT MEASURED**. No paid service was activated. Do not quote a monthly pilot price or margin from synthetic tests.

Existing code enforces 18,000 meeting seconds per owner/month (five hours), private audio bounds and bounded job retries. CI includes simultaneous quota reservations; this proves the counter behavior, not provider invoices or every V2 agent budget.

Before pricing, record provider usage IDs, approved account pricing and actual invoices for 10 meeting hours (across authorized test accounts or an explicitly approved quota change), 100 Ask requests, 25 permitted public-source fetches and real opted-in check-ins. Record transcription/live/embedding/generation usage, retries, storage retention, network transfer and idle web/API/worker/database costs separately. Never bypass the five-hour limit just to run this sample.

Calculate observed cost per completed meeting hour, per answered Ask request, per accepted research result and per delivered check-in. Include failed/uncertain work and provider retries in the numerator. Compute monthly contribution margin only after both actual usage and lawful billing terms are available.

New assistant/research work must enforce owner budgets, a global circuit breaker, finite retries and quiet-hour/frequency caps before enabling providers. These are release requirements, not controls already proven for unimplemented features.
