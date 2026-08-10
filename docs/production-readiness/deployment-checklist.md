# Production Deployment & Infrastructure Checklist

**Date**: August 6, 2026  
**Repository**: `E:\second brain`  
**Deployment Model**: 
- **Frontend**: Next.js App Router on Vercel (`apps/web`)
- **Backend API & MCP**: Unified Python FastAPI container on Render (`apps/api`)
- **Database & Storage**: Supabase PostgreSQL + pgvector + Supabase Auth

---

## 1. Deployment Architecture Summary

```
                       ┌─────────────────────────┐
                       │     Vercel Platform     │
                       │    (Next.js App Router) │
                       │       apps/web          │
                       └───────────┬─────────────┘
                                   │
                    HTTPS REST / SSE / Streamable HTTP
                                   │
                       ┌───────────▼─────────────┐
                       │   Render Web Service    │
                       │  (FastAPI ASGI Docker)  │
                       │       apps/api          │
                       │   /api/v1  +  /mcp      │
                       └───────────┬─────────────┘
                                   │
                   PostgreSQL Connection / Supabase Auth
                                   │
                       ┌───────────▼─────────────┐
                       │   Supabase Cloud DB     │
                       │  (pgvector + Storage)   │
                       └─────────────────────────┘
```

---

## 2. Infrastructure Step-by-Step Checklist

### Phase 1: Database Setup (Supabase)
- [x] Create Supabase Project and verify PostgreSQL 15 connection string.
- [x] Execute Supabase migrations under `supabase/migrations/`.
- [x] Verify pgvector extension is enabled (`CREATE EXTENSION IF NOT EXISTS vector;`).
- [x] Verify RLS is enabled on all production tables.
- [x] Obtain `SUPABASE_URL`, `SUPABASE_ANON_KEY`, and `SUPABASE_SERVICE_ROLE_KEY`.

### Phase 2: Backend API & MCP Deployment (Render)
- [x] Create a single Render Web Service pointing to `apps/api/Dockerfile`.
- [x] Configure Start Command: `uvicorn app.main:app --host 0.0.0.0 --port 8000`.
- [x] Set Environment Variables on Render:
  - `DATABASE_URL`
  - `SUPABASE_URL`
  - `SUPABASE_SERVICE_ROLE_KEY`
  - `JWT_SECRET`
  - `GEMINI_API_KEY`
  - `GOOGLE_CLIENT_ID` & `GOOGLE_CLIENT_SECRET`
  - `CORS_ORIGINS=["https://second-brain.vercel.app"]`
- [x] Confirm deployment health endpoint: `GET https://taj-second-brain-api.onrender.com/health` returns `{"status":"ok"}`.
- [x] Confirm MCP endpoint: `GET https://taj-second-brain-api.onrender.com/mcp` returns `{"status":"online"}`.

### Phase 3: Frontend Deployment (Vercel)
- [x] Connect repository to Vercel and set Root Directory to `apps/web`.
- [x] Set Environment Variables on Vercel:
  - `NEXT_PUBLIC_API_URL=https://taj-second-brain-api.onrender.com`
  - `NEXT_PUBLIC_SUPABASE_URL=https://your-supabase-project.supabase.co`
  - `NEXT_PUBLIC_SUPABASE_ANON_KEY=your-supabase-anon-key`
- [x] Trigger Vercel Production Build (`pnpm --filter web build`).
- [x] Confirm site availability at `https://second-brain.vercel.app`.
