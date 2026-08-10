# Automated P0/P1 Regression Suite Specification

**Suite Name:** Core Founder Journey & Security Gate  
**Execution Time:** ~47 seconds  
**CI Gate Policy:** Must pass 100% prior to main branch merge or release tag.  

---

## 1. Automated Test Roster

```yaml
suite:
  name: Taj's Second Brain P0/P1 Regression Suite
  environment: local_test_db
  execution_command: pytest apps/api/tests && npm run test --prefix apps/web

  modules:
    - name: Authentication & Security Isolation
      file: apps/api/tests/test_auth_security.py
      priority: P0
      cases:
        - test_auth_unauthenticated_access_denied
        - test_auth_valid_jwt_user_isolation
        - test_auth_cross_tenant_rls_boundary

    - name: Founder Execution & Task Management
      file: apps/api/tests/test_founder_domain.py
      priority: P0
      cases:
        - test_create_venture_and_project
        - test_create_task_and_status_transition
        - test_get_dashboard_summary

    - name: CRM, Meetings & Memories
      file: apps/api/tests/test_crm_memory.py
      priority: P1
      cases:
        - test_create_person_and_interaction
        - test_capture_memory_and_vector_embedding
        - test_search_memories_grounding

    - name: Export & Portability Engine
      file: apps/api/tests/test_integrations_export.py
      priority: P0
      cases:
        - test_export_markdown_zip_generation
        - test_export_secret_and_token_redaction

    - name: MCP Protocol Tools
      file: apps/api/tests/test_mcp_api.py
      priority: P0
      cases:
        - test_mcp_tool_discovery
        - test_mcp_token_revocation
```
