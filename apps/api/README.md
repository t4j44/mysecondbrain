# Taj's Second Brain - FastAPI Backend Service

This service provides the enterprise-grade, secure domain application backend for **Taj's Second Brain**. It exposes authenticated APIs for the Next.js frontend, AI processing layer, and Model Context Protocol (MCP) integrations.

## Core Features
- **Strict Authentication & RLS**: Verifies Supabase JWTs locally and applies multi-layered user isolation across all repositories.
- **22 Domain Modules**: Full support for Founder Dashboard, CRM, Ventures, Projects, Tasks, Ideas, Decisions, Memories, Documents, KPIs, Achievements, Portfolio, Content, and Integrations.
- **Hybrid Search & AI Abstraction**: Clean provider interface (`GeminiLLMProvider` / `OpenAILLMProvider`) and RAG retrieval pipelines.
- **Background Jobs**: Persistent database-backed task engine for document ingestion, Markdown knowledge exports, and Google Drive syncing.
- **Structured Error Protocols**: Comprehensive application exception mapping adhering to standard error formats with distributed Request IDs.

## Local Development Setup

1. **Create Virtual Environment**:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   # source .venv/bin/activate  # Linux/Mac
   ```
2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Configure Environment**:
   Copy `.env.example` to `.env` and configure local secrets.

4. **Run Server**:
   ```bash
   uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```

## Testing & Quality Assurance
Run all required tests (unit, repository, service, api, security):
```bash
pytest
ruff check .
mypy app
```
