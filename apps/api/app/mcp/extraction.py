"""
Pre-transaction Work Intelligence extraction for the MCP finalize_work_session tool.

Extraction runs BEFORE any database transaction is opened. Model inference is slow and can
fail; holding a transaction open across it would pin a pooled connection and widen the lock
window for every write in the finalize batch. The MCP tool therefore extracts first, then
opens the RLS-scoped transaction only to validate, dedupe, resolve and write.

Truth rules (G0):
  * When Gemini is unconfigured the deterministic markdown/section parser is used and the
    result is labelled `deterministic`. The offline canned-completion path of
    GeminiLLMProvider is never accepted as an extraction.
  * `quality_validated` is always False here. Extraction accuracy is only a measured number
    once it has been scored against real sessions with a live key
    (see docs/production-recovery/G5_MCP_FINALIZE_GATE.md).
"""

import json
import re
from typing import Any, Dict, List, Optional

from app.ai.provider import GeminiLLMProvider
from app.core.config import settings
from app.core.logging import logger
from app.mcp.tools import parse_markdown_sections

MODE_AI = "gemini"
MODE_DETERMINISTIC = "deterministic"

# Buckets the finalizer persists. Keys match MCPDomainTools.finalize_work_session kwargs.
EXTRACTION_FIELDS = (
    "objective",
    "work_completed",
    "research",
    "findings",
    "decisions",
    "rationale",
    "rejected_alternatives",
    "tasks",
    "people_mentioned",
    "organizations_mentioned",
    "commitments",
    "evidence",
    "source_references",
    "artifacts",
    "skills_demonstrated",
    "portfolio_candidates",
    "unresolved_questions",
)

_SCALAR_FIELDS = frozenset({"objective", "rationale"})

_EXTRACTION_INSTRUCTION = (
    "You are a Work Intelligence extractor for a founder's second brain. Read the work "
    "session transcript and return ONLY a JSON object, no prose and no code fences, with "
    "exactly these keys: objective (string), work_completed (string[]), research (string[]), "
    "findings (string[]), decisions (object[] with decision, context, rationale, "
    "rejected_alternatives[]), rationale (string), rejected_alternatives (string[]), tasks "
    "(object[] with title, description, priority, due_date), people_mentioned (object[] with "
    "name, role, company), organizations_mentioned (string[]), commitments (string[]), "
    "evidence (string[]), source_references (string[]), artifacts (string[]), "
    "skills_demonstrated (string[]), portfolio_candidates (object[] with title, "
    "problem_statement), unresolved_questions (string[]). Never invent facts that are not in "
    "the transcript. Use an empty array or empty string when a bucket has no evidence."
)


def _session_text(summary: Optional[str], session_payload: Optional[Dict[str, Any]]) -> str:
    """Flatten the low-friction input into one transcript the extractor can read."""
    parts: List[str] = []
    if summary:
        parts.append(str(summary))
    payload = session_payload or {}
    for key in ("summary", "transcript", "conversation", "notes", "messages", "text"):
        value = payload.get(key)
        if not value:
            continue
        if isinstance(value, str):
            parts.append(value)
        elif isinstance(value, list):
            for entry in value:
                if isinstance(entry, str):
                    parts.append(entry)
                elif isinstance(entry, dict):
                    content = entry.get("content") or entry.get("text") or ""
                    role = entry.get("role") or entry.get("author") or ""
                    if content:
                        parts.append(f"{role}: {content}".strip(": "))
    return "\n".join(p for p in parts if p).strip()


def deterministic_extraction(
    summary: Optional[str], session_payload: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """Section/bullet parser used offline and as the fallback when inference fails."""
    payload = session_payload or {}
    sections = parse_markdown_sections(_session_text(summary, session_payload))

    def bucket(*names: str) -> List[Any]:
        for name in names:
            value = payload.get(name) or sections.get(name)
            if value:
                return list(value)
        return []

    return {
        "objective": payload.get("objective") or "",
        "work_completed": bucket("work_completed"),
        "research": bucket("research"),
        "findings": bucket("findings"),
        "decisions": bucket("decisions"),
        "rationale": payload.get("rationale") or "",
        "rejected_alternatives": bucket("rejected_alternatives"),
        "tasks": bucket("tasks"),
        "people_mentioned": bucket("people_mentioned", "people"),
        "organizations_mentioned": bucket("organizations_mentioned", "organizations"),
        "commitments": bucket("commitments"),
        "evidence": bucket("evidence"),
        "source_references": bucket("source_references"),
        "artifacts": bucket("artifacts"),
        "skills_demonstrated": bucket("skills_demonstrated", "skills"),
        "portfolio_candidates": bucket("portfolio_candidates", "portfolio"),
        "unresolved_questions": bucket("unresolved_questions", "questions"),
    }


def _coerce(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Keep only known buckets and force each into the shape the finalizer expects."""
    coerced: Dict[str, Any] = {}
    for field in EXTRACTION_FIELDS:
        value = raw.get(field)
        if field in _SCALAR_FIELDS:
            coerced[field] = str(value).strip() if isinstance(value, (str, int, float)) else ""
        elif isinstance(value, list):
            coerced[field] = [v for v in value if v not in (None, "", {}, [])]
        elif isinstance(value, (str, dict)) and value:
            coerced[field] = [value]
        else:
            coerced[field] = []
    return coerced


def _parse_model_json(text: str) -> Dict[str, Any]:
    candidate = text.strip()
    fenced = re.search(r"```(?:json)?\s*(.+?)```", candidate, re.DOTALL)
    if fenced:
        candidate = fenced.group(1).strip()
    else:
        start, end = candidate.find("{"), candidate.rfind("}")
        if start != -1 and end > start:
            candidate = candidate[start : end + 1]
    parsed = json.loads(candidate)
    if not isinstance(parsed, dict):
        raise ValueError("Extraction response was not a JSON object.")
    return parsed


def _merge(primary: Dict[str, Any], fallback: Dict[str, Any]) -> Dict[str, Any]:
    """Model output wins per bucket; empty buckets fall back to the deterministic parse."""
    return {field: (primary.get(field) or fallback.get(field)) for field in EXTRACTION_FIELDS}


async def extract_session_intelligence(
    *,
    summary: Optional[str] = None,
    session_payload: Optional[Dict[str, Any]] = None,
    provider: Optional[str] = None,
    user_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Extract Work Intelligence buckets from a session transcript without touching the database.

    Returns {"fields": {...finalizer kwargs...}, "extraction": {...provenance...}}.
    Never raises: a failed inference degrades to the deterministic parse and is reported.
    """
    fallback = deterministic_extraction(summary, session_payload)
    transcript = _session_text(summary, session_payload)
    telemetry: Dict[str, Any] = {
        "mode": MODE_DETERMINISTIC,
        "model": None,
        "provider": provider or "mcp_client",
        "transcript_chars": len(transcript),
        "error": None,
        "quality_validated": False,
    }

    llm = GeminiLLMProvider()
    if not transcript:
        telemetry["error"] = "Empty session transcript; nothing to extract."
        return {"fields": fallback, "extraction": telemetry}
    if llm._is_unconfigured():
        telemetry["error"] = "GEMINI_API_KEY is unconfigured; AI extraction unavailable."
        return {"fields": fallback, "extraction": telemetry}

    try:
        from app.ai.privacy import private_ai_scope
        from app.dependencies.database import rls_db_session
        if user_id is None:
            raise ValueError('Authenticated owner is required for AI extraction.')
        # Load the alias dictionary under RLS, then release the read transaction
        # before inference and before the finalizer's atomic write transaction.
        with private_ai_scope(user_id) as privacy:
            async with rls_db_session(user_id) as db:
                privacy.db = db
                await privacy.load()
            privacy.db = None
            response = await llm.generate_content(
                prompt=transcript, system_instruction=_EXTRACTION_INSTRUCTION,
            )
        extracted = _merge(_coerce(_parse_model_json(response)), fallback)
        telemetry["mode"] = MODE_AI
        telemetry["model"] = settings.GEMINI_MODEL
        return {"fields": extracted, "extraction": telemetry}
    except Exception as exc:  # inference/parse failure must never lose the session
        logger.warning('MCP extraction unavailable (%s); using deterministic parse', type(exc).__name__)
        telemetry["error"] = type(exc).__name__
        return {"fields": fallback, "extraction": telemetry}


__all__ = [
    "EXTRACTION_FIELDS",
    "MODE_AI",
    "MODE_DETERMINISTIC",
    "deterministic_extraction",
    "extract_session_intelligence",
]
