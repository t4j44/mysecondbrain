# Database Package & Generated Types — Taj's Second Brain

This package (`packages/database/`) serves as the canonical shared repository for generated database type definitions, schema migrations, and alignment tools across frontend (TypeScript/Next.js) and backend (Python/FastAPI) applications.

---

## Structure
- `generated/types.ts`: Generated TypeScript interface definitions for Supabase JavaScript/SSR SDKs.
- `generated/pydantic_models.py`: Python Pydantic ORM structural alignment contracts for FastAPI service routers.

---

## Regenerating Types from Schema

### For TypeScript (Next.js Application)
Run the Supabase CLI generator command when database migrations change:
```bash
npx supabase gen types typescript --local > generated/types.ts
```

### For Python (FastAPI Backend Application)
Ensure Pydantic models stay synchronized with PostgreSQL column specifications without manual copy-pasting:
```bash
python -m datamodel_code_generator --input-file http://localhost:54321/ --input-file-type openapi --output generated/pydantic_models.py
```
