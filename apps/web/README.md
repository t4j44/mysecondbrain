# Taj’s Second Brain // Frontend Web Application (`apps/web`)

Welcome to the Next.js App Router web application console for **Taj’s Second Brain**. Built by **Agent 4**, this repository provides the complete frontend architecture, authenticated layout shells, design system primitives, and testing foundations for all future feature modules.

---

## Quickstart & Local Environment Setup

### 1. Configure Environment Variables
Copy the template file in `apps/web/` to initialize your local runtime secrets:
```bash
cp .env.example .env.local
```
Ensure your `.env.local` includes valid URL metrics matching your local Supabase instance and FastAPI backend:
```ini
NEXT_PUBLIC_SUPABASE_URL=http://127.0.0.1:54321
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOi...
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_SITE_URL=http://localhost:3000
```
*(Note: Runtime environment variables are verified upon server startup via `lib/env.ts` using Zod validation).*

### 2. Install dependencies & Run Development Server
From the root monorepo directory:
```bash
# Install workspace dependencies via pnpm
pnpm install

# Start local Next.js developer console on port 3000
pnpm --filter web dev
```
Navigate your browser to `http://localhost:3000` to interact with the console terminal.

---

## Verification & Testing Commands

To execute quality checks and run automated frontend unit test suites:
```bash
# Run Vitest React Component & Auth Utility Test Suites
pnpm --filter web test

# Validate TypeScript type consistency across all modules
pnpm --filter web typecheck

# Verify ESLint code consistency
pnpm --filter web lint

# Execute production build compilation test
pnpm --filter web build
```

---

## Documentation Roadmap

For in-depth integration instructions, refer to the project technical guides located in `docs/frontend/`:
- **[Frontend Architecture & Integration Patterns](../../docs/frontend/architecture.md)**: Details Supabase SSR middleware rules, FastAPI REST client error tracing, and React Query caching protocols.
- **[Retro-Futuristic Design System Manual](../../docs/frontend/design-system.md)**: Explains color palettes, typography hierarchies, reusable UI primitives, and WCAG accessibility standards.
