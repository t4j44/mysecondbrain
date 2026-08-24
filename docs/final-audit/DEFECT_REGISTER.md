# SECTION 31 — PRIORITY DEFECT REGISTER

### P0 (Prevents daily use/security)
*   **None discovered that completely break the existing implemented flow.** Security headers, JWT checks, RLS policies, and token scopes are fundamentally sound.

### P1 (Important broken capability)
*   **Fake Google Integrations**:
    *   **Issue**: Google Drive, Calendar, and Contacts integrations are fully simulated. They return fake tokens (`1//0e_simulated_refresh_token...`) and hardcoded success metrics (`{"synced_files_count": 14}`).
    *   **Root Cause**: `apps/api/app/integrations/google_client.py` and `apps/api/app/jobs/handlers/sync_google.py` use mock logic.
    *   **Affected Files**: `google_client.py`, `sync_google.py`.
    *   **Dependencies**: Google APIs, OAuth2 flow.
    *   **Estimated Complexity**: High. Requires actual OAuth implementation, refresh token handling, and robust third-party API interaction logic.
    *   **Recommended Fix Order**: 1. This invalidates a large portion of the "Network Intelligence" and external productivity promise.

*   **Missing standalone MCP Server**:
    *   **Issue**: Documentation claims `apps/mcp-server` exists as a sidecar, but it does not. The MCP server is mounted inside FastAPI at `/mcp`.
    *   **Root Cause**: Architectural pivot without documentation update.
    *   **Affected Files**: `README.md`, `integration_status.md`.
    *   **Estimated Complexity**: Low (documentation fix) or High (if extraction is actually required).
    *   **Recommended Fix Order**: 2. Update docs to reflect current truth.

### P2 (Improvement)
*   **Frontend Empty States & Stubs**:
    *   **Issue**: The frontend is heavily populated with empty states waiting for future "Agents" (e.g. Agent 5, Agent 6). Most CRUD operations in the UI are stubbed to trigger toasts rather than hitting the heavily developed backend.
    *   **Root Cause**: Frontend development lagging significantly behind backend API implementation.
    *   **Affected Files**: `apps/web/app/(dashboard)/ventures`, `tasks`, `people`, etc.
    *   **Estimated Complexity**: Medium to High (Frontend wiring).
    *   **Recommended Fix Order**: 3. Connect the existing, tested API endpoints to the UI components.

*   **Orphaned Backend Endpoints**:
    *   **Issue**: Deprecated endpoints exist in `app/_quarantine/endpoints/dashboard.py`.
    *   **Root Cause**: Legacy code not removed.
    *   **Affected Files**: `dashboard.py`.
    *   **Estimated Complexity**: Low.
    *   **Recommended Fix Order**: 4. Delete the quarantine folder.

### P3 (Future)
*   **Column Type Drift (SQLAlchemy vs Supabase)**:
    *   **Issue**: Complex column types (`PG_ARRAY`, `JSON`) might cause schema drift.
    *   **Root Cause**: Inherent friction between SQLAlchemy and Supabase/PostgreSQL.
    *   **Affected Files**: `packages/database`, `scratch_colspec.py`.
    *   **Estimated Complexity**: Medium.
    *   **Recommended Fix Order**: 5. Standardize synchronization tooling.
