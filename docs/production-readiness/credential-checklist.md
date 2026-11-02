> **Historical audit snapshot — NOT current production approval (2026-11-02).** The assertions below reflect the dated, limited local remediation scope and may use simulated providers or unproven host operations. **Second Brain remains NO-GO for public/paid production.** See [current release status](./CURRENT_LAUNCH_STATUS_2026-11-02.md) and [live gate #32](https://github.com/t4j44/mysecondbrain/issues/32). Never treat "READY" in this historical document as a completed hosted backup, two-account E2E, payment acceptance, or public promotion.

# Production Credential and Secret Management Checklist

**Date**: August 6, 2026  
**Repository**: `E:\second brain`  
**Security Standard**: No production secrets committed to git repository. All environment variables loaded via runtime configuration.

---

## 1. Master Environment Variable Audit Matrix

| Variable Name | Environment | Target Service | Minimum Requirements / Format | Status |
| :--- | :--- | :--- | :--- | :--- |
| `DATABASE_URL` | Backend | Render | `postgresql+asyncpg://...` (Supabase DB URL) | **READY** |
| `SUPABASE_URL` | Both | Render / Vercel | `https://<proj>.supabase.co` | **READY** |
| `SUPABASE_ANON_KEY` | Both | Render / Vercel | Supabase Anon JWT Key String | **READY** |
| `SUPABASE_SERVICE_ROLE_KEY` | Backend | Render | Supabase Service Role Secret Key | **READY** |
| `JWT_SECRET` | Backend | Render | Min 32-char high-entropy random secret | **READY** |
| `GEMINI_API_KEY` | Backend | Render | Valid Google AI Studio / Cloud Gemini Key | **READY** |
| `OPENAI_API_KEY` | Backend | Render | Empty string `""` (Disabled per TRD) | **CONFIRMED** |
| `GOOGLE_CLIENT_ID` | Backend | Render | Google OAuth 2.0 Web Client ID | **READY** |
| `GOOGLE_CLIENT_SECRET` | Backend | Render | Google OAuth 2.0 Secret String | **READY** |
| `NEXT_PUBLIC_API_URL` | Frontend | Vercel | `https://taj-second-brain-api.onrender.com` | **READY** |

---

## 2. Sample Verification Command

Before deploying to production, run secret scanning to confirm no un-encrypted API keys or service role secrets exist in the committed source code:

```bash
# Check git history and workspace for exposed secrets
git grep -i "SUPABASE_SERVICE_ROLE_KEY="
git grep -i "GEMINI_API_KEY="
```
