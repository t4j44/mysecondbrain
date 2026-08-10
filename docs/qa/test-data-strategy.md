# Test Data Strategy & Synthetic Data Architecture

**Target Release:** v1.0.0-RC1  
**Policy:** 100% Synthetic Fictional Data — Zero Production Persona Usage  

---

## 1. Test Data Generation Principles

1. **Strict Anonymization & Fictional Personas**:
   - All test users, contacts, ventures, and interactions utilize generated fictional names (e.g., `Taj TestFounder`, `Alex VenturePartner`, `Justor AI Test`).
2. **Deterministic Test Fixtures**:
   - Seed data populated via `conftest.py` Pytest fixtures ensuring reproducible state across test invocations.
3. **Data Teardown & Isolation**:
   - Automated test database teardown routines execute after every test module run to prevent persistent dirty state.

---

## 2. Seed Data Profiles & Entity Counts

| Entity Type | Synthetic Count | Purpose | Teardown Strategy |
|---|---|---|---|
| **Users / Profiles** | 2 (`user_a`, `user_b`) | Cross-tenant RLS isolation testing | DB Transaction Rollback |
| **Ventures** | 4 (`Justor AI`, `Zqtion`, `IEXF`, `CMOOS`) | Venture portfolio & roadmap testing | Fixture Cleanup |
| **Projects** | 6 | Task group & execution testing | Cascade Delete |
| **Tasks** | 20 | Kanban board & priority filter testing | Cascade Delete |
| **CRM Contacts (People)** | 10 | Relationship & interaction tracking | Cascade Delete |
| **Interactions & Meetings**| 15 | Timeline & note analysis testing | Cascade Delete |
| **Vector Memories** | 25 | `pgvector` similarity search & RAG grounding | Vector Table Truncation |
| **Ideas & KPIs** | 8 | Idea analysis & KPI telemetry testing | Fixture Teardown |
