# Taj’s Second Brain // Frontend Architecture Guide

This document defines the frontend architecture, system boundaries, integration patterns, and conventions for **Taj’s Second Brain** (Agent 4 implementation). All feature developers and AI sub-agents (Agents 5 through 9) must adhere to these structural guidelines when expanding the web console.

---

## 1. System Overview & Monorepo Layout

The frontend resides within an enterprise-grade `pnpm` workspace monorepo.

```
second-brain/
├── apps/
│   └── web/                   # Primary Next.js App Router Web Application
│       ├── app/               # App Router pages, layouts, and route handlers
│       │   ├── (auth)/        # Authentication routes (unprotected / guest only)
│       │   └── (dashboard)/   # Protected operator console routes (RLS enforced)
│       ├── components/        # Frontend functional UI components
│       │   ├── layout/        # AppShell, Sidebar, TopBar, Mobile Drawer, CommandMenu
│       │   ├── shared/        # Reusable product components (PageHeader, EmptyState, AIInsightPanel)
│       │   └── ui/            # Accessible primitive building blocks (Button, Input, Card, Badge)
│       ├── lib/               # Singleton utilities, environment validation, auth, and API clients
│       ├── providers/         # Global React Query and Next-Themes wrappers
│       └── __tests__/         # Vitest unit and component validation test suites
├── packages/
│   ├── shared-types/          # Monorepo database contracts, domain entity types, and enums
│   └── config/                # Shared TypeScript, ESLint, and PostCSS configs
└── docs/                      # Comprehensive technical implementation manuals
```

---

## 2. Supabase Authentication & Security Enclosure

Authentication in Taj’s Second Brain relies on **Supabase Auth** integrated via `@supabase/ssr` to guarantee rock-solid Server-Side Rendering (SSR) and HTTP-only cookie session persistence.

### Three-Client Architecture
1. **Browser Client (`lib/supabase/client.ts`)**: Singleton Supabase browser client running client-side for immediate user state interactions and login form submission.
2. **Server Client (`lib/supabase/server.ts`)**: Invoked within Next.js React Server Components (RSCs) and Server Actions to read authenticated JWT cookies securely without exposing secrets to client bundles.
3. **Middleware Guard (`lib/supabase/middleware.ts` & `middleware.ts`)**: Executes before every Next.js request. Refreshes expired auth cookies automatically and enforces strict routing enclosures:
   - Unauthenticated access attempts to `/dashboard/**` or `/settings/**` are redirected instantly to `/login`.
   - Authenticated sessions attempting to hit `/login` or `/signup` are fast-routed back to `/dashboard`.

### Zero-Exposure Secret Rule
The web frontend must **NEVER** import or contain `SUPABASE_SERVICE_ROLE_KEY`. All database mutations execute strictly under the operator’s authenticated JWT user claims (`auth.uid()`), fully protected by PostgreSQL Row-Level Security (RLS) rules established by Agent 2.

---

## 3. FastAPI Backend Client Integration

To isolate computationally heavy domain logic (AI vector RAG, Whisper audio extraction, analytics), the frontend interacts with our Python FastAPI backend (Agent 3) through a typed REST client located in `lib/api/client.ts`.

### Key Capabilities:
- **Automatic JWT Injection**: The `FastApiClient` dynamically attaches the operator's Supabase session Bearer token (`Authorization: Bearer <jwt>`) to all HTTP requests.
- **Wrapped Data Unwrapping**: Our FastAPI backend adheres to a standard API envelope:
  ```json
  { "data": { ... }, "meta": { "timestamp": 1722800000 } }
  ```
  The `FastApiClient.get<T>()` and `.post<T>()` methods automatically unwrap the `.data` property, returning strongly-typed domain interfaces to components.
- **Structured Error Tracing**: When an HTTP error occurs, the client extracts the error code and `request_id`, converting them into an `ApiError` instance. UI Error State components display this Request ID for tracing debug logs without exposing Python server stack traces to terminal users.

---

## 4. State Management Strategy

1. **Server State (TanStack React Query v5)**: All external data querying from FastAPI and asynchronous database fetches must flow through React Query hooks (`useQuery`, `useMutation`). Configured in `providers/query-provider.tsx` with automatic exponential retry backoff (skipping 401/403/404 errors) and a 5-minute cache freshness duration.
2. **UI Operational State (React Context & Local State)**: Ephemeral interface states (drawer toggle status, active tab index, command search string) remain localized using simple React `useState` and native context to prevent global store bloat.
3. **Url-State (Next.js Navigation)**: Filter parameters, Search queries in lists, and deep links are stored directly in URL query parameters using `useSearchParams()`, enabling bookmarkable executive console views.

---

## 5. Route Handling & Fallback Foundations

All route segments under `app/(dashboard)/` inherit proactive defensive boundaries:
- **`loading.tsx`**: Triggers skeleton grid approximations immediately upon route navigation while React Server Components await async database or API queries.
- **`error.tsx`**: Isolates segment crashes. If a feature module fails, the surrounding AppShell (Sidebar & TopBar) remains fully operational, presenting an interactive retry prompt with API Request ID tracing.
- **`not-found.tsx`**: Renders a custom terminal themed Sector Not Found page when invalid entity coordinates or unmapped feature routes are requested.
