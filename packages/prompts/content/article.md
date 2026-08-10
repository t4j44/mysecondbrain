# Long-Form Technical Article & Thought Leadership Prompt
**Prompt Version:** 1.0.0  
**Target Model:** Gemini 1.5 Pro (`gemini-1.5-pro`)  
**Module:** AI Content Engine (`/api/v1/content/generate`)

---

## 1. Purpose
Synthesize technical research notes, architectural decision ledgers (ADRs), execution experiences, and deep product hypotheses into high-signal, publication-ready engineering articles or thought leadership essays.

---

## 2. Input Schema (JSON)
```json
{
  "content_type": "article",
  "topic": "Designing Multi-Agent Software Engineering Workflows with RAG",
  "target_audience": "Software Architects, Senior Developers, & AI Product Leaders",
  "structure_preference": "generate_outline_first | comprehensive_draft",
  "source_records": [
    { "id": "UUID", "type": "decision | document_chunk | memory", "title": "string", "content": "string" }
  ]
}
```

---

## 3. Grounding & Composition Rules
1. **NO VERBATIM DOCUMENT DUMPING:** Do not copy raw internal 500-token chunks verbatim; synthesize insights into clean, publication-ready technical prose while maintaining internal citation links.
2. **MAINTAIN TECHNICAL ACCURACY:** Respect specific database extensions (`pgvector`), architectural patterns (Wrapped Resource Responses, RRF Hybrid Search), and domain terminology exactly as presented in source documentation.
3. **NO FICTITIOUS BENCHMARKS:** Do not invent latency benchmarks (e.g., "our query execution time dropped to 3ms") unless confirmed by explicit diagnostic records or performance test notes in the source input.

---

## 4. Required Output Schema (JSON)
```json
{
  "title": "Architecting Zero-Hallucination Multi-Agent Workflows in Supabase & FastAPI",
  "outline": [
    "1. The Challenge of Parallel Agent Coordination",
    "2. Enforcing Ownership via Row Level Security (RLS) and Constrained Text Fields",
    "3. Hybrid RAG Search using Reciprocal Rank Fusion (RRF)"
  ],
  "body": "## 1. The Challenge of Parallel Agent Coordination\nAs autonomous agents take on increasingly complex software engineering tasks...",
  "word_count": 820,
  "citations": [
    { "source_id": "UUID", "concept_supported": "ADR-011 evaluation of PostgreSQL Enums vs CHECK constraints" }
  ]
}
```
