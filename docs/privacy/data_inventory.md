# Privacy Architecture & Data Inventory — Taj's Second Brain

Version: 1.0  
Author: Agent 11 — Security, Privacy, DevSecOps, SRE & Production Readiness Agent  
Date: 2026-08-05  

---

## 1. System Data Inventory

| Domain / Asset | Data Classification | Storage Location | Retention Period | Exposed to AI RAG? | Included in Export? | Hard Deletion Support? |
|---|---|---|---|---|---|---|
| User Credentials | Sensitive Auth | `auth.users` (Supabase) | Account Lifetime | NO | NO | YES (Immediate) |
| Ventures & Projects | Confidential IP | `public.ventures`, `projects` | User Managed | YES (Filtered) | YES (Markdown) | YES (Cascade) |
| CRM & Contacts | PII / Confidential | `public.people`, `interactions` | User Managed | YES (Filtered) | YES (Markdown) | YES (Cascade) |
| Notes & Memories | Private Knowledge | `public.memories` | User Managed | YES (Top-K) | YES (Markdown) | YES (Cascade) |
| Vector Embeddings | Derived Knowledge | `public.memory_embeddings` | Regenerated | YES | NO | YES (Cascade) |
| Uploaded Documents | Business Files | Supabase Storage (Private) | User Managed | YES (Chunks) | YES (Binary) | YES (Immediate) |
| OAuth Tokens | High Secret | `public.integrations` (AES-256) | Connection Lifetime | NO | NO | YES (Revoked + Wiped) |
| Audit Logs | System Audit | `public.audit_logs` | 90 Days | NO | NO | YES (Account Delete) |

---

## 2. Retention, Deletion & Account Erasure

### Comprehensive Account Destruction Routine
When a user requests account erasure (`DELETE /api/v1/user/account`):
1. **Google Integrations**: Invokes remote revocation endpoints (`https://oauth2.googleapis.com/revoke`) for active OAuth refresh tokens.
2. **Storage Wipe**: Deletes all user-owned binary Blobs across all private Supabase Storage buckets.
3. **Database Cascade**: Deletes user record in `auth.users`, triggering PostgreSQL `ON DELETE CASCADE` across all 56 domain tables (including embeddings, notes, CRM contacts, and audit trails).
4. **Local Workspace Cleanup**: Removes any cached export zip archives on local disks.
