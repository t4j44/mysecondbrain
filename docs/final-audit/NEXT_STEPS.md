# SECTION 33 — NEXT DEVELOPMENT ROADMAP

## NEXT 24 HOURS
1. **Acknowledge the Fake Google Integrations**: Stop referring to Google Calendar/Drive/Contacts as "implemented" in documentation. Change status to "Mocked/Planned".
2. **Update Architectural Documentation**: Correct `README.md` and `api_contracts.md` to reflect that the MCP server is mounted inside FastAPI at `/mcp`, and `apps/mcp-server` does not exist.
3. **Delete Quarantine Code**: Remove `apps/api/app/_quarantine/endpoints/dashboard.py` to prevent accidental re-introduction of legacy code.

## NEXT 3 DAYS
1. **Wire Frontend Tasks & Ventures**: Replace the stub buttons ("+ CREATE TASK", "+ PROVISION VENTURE") in the Next.js UI with real React Query mutations hitting the existing, tested `apps/api/app/api/v1/endpoints/founder.py` routes.
2. **Wire Frontend CRM (People)**: Replace the "+ ADD CONTACT" stub in `apps/web/app/(dashboard)/people` with real API calls.
3. **Verify Deployment Configuration**: Ensure the FastAPI CORS settings and Vercel environment variables correctly map to allow Next.js to authenticate and route to the backend.

## NEXT 7 DAYS
1. **Implement Real Google OAuth**: Replace the mocked `google_client.py` with an actual OAuth2 flow using `google-auth` and `google-api-python-client`.
2. **Implement Real Google Calendar Sync**: Write the actual API calls in `sync_google.py` to push tasks with due dates to a designated Google Calendar.
3. **Frontend Markdown Export Trigger**: Build a UI component in the Next.js Settings panel to trigger the `/api/v1/system/export` route and download the generated Markdown archive.

## NEXT 30 DAYS
1. **Full RAG UI Integration**: Build out the `/documents` and `/memories` UI to support file uploads, piping them to the `pdf_analysis.py` endpoints, and displaying chunking/embedding progress.
2. **Portfolio Generator UI**: Connect the `ai_portfolio` endpoints to a frontend interface, allowing the user to select achievements and review the generated "Draft" case studies before marking them verified.
3. **Complete Mobile PWA Polish**: Ensure all newly wired data tables and forms are fully responsive and functional on iOS/Android viewports.
