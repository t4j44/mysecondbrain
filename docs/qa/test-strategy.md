# Test Strategy & Quality Architecture — Taj's Second Brain

**Version:** 1.0  
**Author:** Agent 12 — Principal QA Architect  
**Target Release:** v1.0.0-RC1  
**Last Updated:** 2026-08-05  

---

## 1. Executive Summary & Quality Vision

Taj's Second Brain is a private, AI-native founder operating system that manages sensitive intellectual property, personal CRM relationships, financial KPIs, strategic ventures, and vector-embedded long-term memories. 

The primary objective of the Quality Assurance architecture is to ensure that Taj's Second Brain is:
1. **Strictly Isolated**: Multi-user and multi-tenant data isolation enforced at the database level (RLS) with zero tolerance for cross-user data leaks or secret exposure.
2. **Contract Compliant**: Strict adherence to OpenAPI schemas, Pydantic backend models, and TypeScript frontend types.
3. **AI-Grounded**: Zero hallucination on personal factual claims, precise attribution/citations, and prompt-injection resilience.
4. **Accessible & Responsive**: Fully usable via keyboard navigation, screen readers (WCAG 2.1 AA compliant), and responsive down to mobile viewports.
5. **Portable & Recoverable**: Reliable Markdown/YAML export with zero vendor lock-in and seamless restoration options.

---

## 2. Testing Pyramid & Verification Layers

```
             / \
            /   \  E2E / Browser Tests (Playwright / Cypress)
           /-----\
          /       \  Integration & Service Tests (Pytest / FastAPI / Vitest)
         /---------\
        /           \  Contract & API Schema Validation (Pydantic / OpenAPI)
       /-------------\
      /               \  Security, RLS & Isolation Tests (Postgres SQL / Supabase)
     /-----------------\
    /                   \  Unit Tests (Pytest / Vitest / Component Specs)
   -----------------------
```

### Layer 1: Unit & Component Testing
- **Backend**: Pytest suite for domain models, utility functions, Pydantic schema validation, and sanitization logic.
- **Frontend**: Vitest + React Testing Library for UI components, form validation, theme state, and custom hooks.

### Layer 2: Security & RLS Policy Testing
- **Database**: Automated SQL scripts (`supabase test db`) verifying Row Level Security (RLS) policies on all 24 public tables.
- **Access Boundary**: Verification that `authenticated` users can only read, write, update, and delete their own records (`user_id = auth.uid()`), while `anon` users have zero access.

### Layer 3: API Contract & Microservice Integration
- **FastAPI Endpoints**: Comprehensive test coverage across all REST endpoints defined in `api_contracts.md`.
- **Error Handling**: Standardized RFC 7807 error format, correlation request IDs, and rate limit header verification.

### Layer 4: AI & Vector RAG Grounding
- **Grounding Verification**: Evaluation set checking that AI response claims map directly to retrieved context chunks.
- **Prompt Injection Defense**: Testing untrusted user inputs (meeting notes, documents, web clips) to verify they cannot subvert system instructions or leak system prompts.

### Layer 5: End-to-End & Browser Automation
- **Playwright Suite**: Cross-browser automated workflows testing the full Founder Journey: Auth -> Dashboard -> Ventures -> CRM -> Memory Search -> AI Generation -> Export.

---

## 3. Defect Severity & Priority Matrix

| Severity | Description | SLA / Action |
|---|---|---|
| **Critical** | Cross-user data access, Auth bypass, Data corruption, Secret leak, AI safety violation, Core workflow crash. | Immediate P0 release blocker. |
| **High** | Feature non-functional, broken pagination, failed export generation, missing validation error. | Must fix prior to v1.0 release. |
| **Medium** | Minor UI alignment defect, non-blocking error display, suboptimal performance. | Fix in next sprint / RC iteration. |
| **Low / Cosmetic** | Typo, minor styling discrepancy, non-critical telemetry missing. | Backlog task. |

---

## 4. Test Execution & Automation Strategy

All automated test suites run across local development, pre-commit hooks, and GitHub Actions CI pipelines:
- `pytest`: Backend domain, integration, and security tests.
- `vitest`: Frontend component and client state unit tests.
- `tsc --noEmit`: Strict TypeScript static type checking.
- `ruff`: Python static analysis and code hygiene.
- `playwright test`: End-to-end browser automation workflows.
