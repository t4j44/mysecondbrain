"""Server-only, request-scoped AI data minimization. Never logs originals or mappings.

Pseudonymization is not anonymization. The UI must disclose residual risk. Raw
attachments and high-risk text are refused in free mode, not sent for redaction.
"""

import hashlib
import hmac
import json
import re
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Any, Iterator

from app.core.config import settings
from app.core.errors import AppError

_scope: ContextVar[Any] = ContextVar("ai_private_scope", default=None)
_HIGH_RISK = re.compile(
    r"(?i)(-----BEGIN .{0,30}PRIVATE KEY|\b(?:password|api[_ -]?key|access[_ -]?token|"
    r"refresh[_ -]?token|secret)\s*[:=]|\b(?:strictly confidential|trade secret|"
    r"attorney.client privileged|medical record|passport number|national id|credit card)\b)"
)
_EMAIL = re.compile(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}")
_PHONE = re.compile(r"(?<!\w)\+?\d[\d ()-]{7,}\d(?!\w)")
_URL = re.compile(r"https?://\S+", re.I)
_UUID = re.compile(r"\b[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}\b", re.I)
_TOKEN = re.compile(r"\b(?:AIza[\w-]{20,}|eyJ[\w-]+\.[\w-]+\.[\w-]+)\b")
_PROPER = re.compile(r"\b[A-Z][a-z]{2,}(?:[ \t]+[A-Z][\w-]{1,}){0,3}\b")


class PrivacyBlocked(AppError):  # noqa: N818
    def __init__(self, reason: str = "sensitive_content"):
        super().__init__(
            "This content stays private. Remove sensitive details before using free-tier AI.",
            code="AI_PRIVACY_BLOCKED", status_code=422, details={"reason": reason},
        )


@dataclass
class PrivateContext:
    user_id: str
    db: Any = None
    aliases: dict[str, str] = field(default_factory=dict)
    reverse: dict[str, str] = field(default_factory=dict)
    sent: set[str] = field(default_factory=set)
    loaded: bool = False

    def alias(self, value: str, kind: str = "ENTITY", identity: str | None = None) -> str:
        digest = hmac.new(
            settings.TOKEN_ENCRYPTION_KEY.encode(),
            f"{self.user_id}:{kind}:{identity or value.casefold()}".encode(), hashlib.sha256,
        ).hexdigest()[:20]
        token = f"[{kind}_{digest}]"
        self.aliases[value] = token
        self.reverse[token] = value
        return token

    async def load(self) -> None:
        if self.loaded or self.db is None:
            return
        from sqlalchemy import select

        from app.models.entities import Organization, Person, Project, Venture

        for model, kind in ((Person, "PERSON"), (Organization, "ORG"),
                            (Project, "PROJECT"), (Venture, "VENTURE")):
            rows = await self.db.execute(select(model.id, model.name).where(
                model.user_id == self.user_id, model.deleted_at.is_(None),
            ))
            for identity, name in rows:
                if name and len(name.strip()) > 1:
                    self.alias(name.strip(), kind, str(identity))
        self.loaded = True

    def minimize(self, text: str) -> str:
        if _HIGH_RISK.search(text) or _TOKEN.search(text):
            raise PrivacyBlocked()
        # Remove contact details BEFORE replacing names; a person's name can also
        # be the local part of an email address and must not break its detector.
        for pattern, replacement in ((_EMAIL, "[EMAIL]"), (_PHONE, "[NUMBER]"),
                                     (_URL, "[LINK]"), (_UUID, "[RECORD]")):
            text = pattern.sub(replacement, text)
        # Resolve longest names first; replacements never carry raw primary keys.
        for name, token in sorted(self.aliases.items(), key=lambda pair: -len(pair[0])):
            text = re.sub(r"(?<!\w)" + re.escape(name) + r"(?!\w)",
                          token, text, flags=re.I)
        # Unknown proper-name candidates get request-scoped aliases too. This is
        # deliberately conservative and is not a general multilingual PII detector.
        text = _PROPER.sub(lambda m: self.alias(m.group(), "LABEL"), text)
        self.sent.update(token for token in self.reverse if token in text)
        return text

    def restore(self, text: str) -> str:
        # Only resolve tokens actually sent in THIS user's request. Unknown or
        # forged placeholders are never looked up globally.
        def restore_value(value):
            if isinstance(value, str):
                for token in self.sent:
                    value = value.replace(token, self.reverse[token])
                return value
            if isinstance(value, list):
                return [restore_value(item) for item in value]
            if isinstance(value, dict):
                return {key: restore_value(item) for key, item in value.items()}
            return value
        candidate = text.strip().removeprefix('```json').removeprefix('```').removesuffix('```').strip()
        try:
            parsed = json.loads(candidate)
        except (ValueError, TypeError):
            return restore_value(text)
        return json.dumps(restore_value(parsed), ensure_ascii=False)


@contextmanager
def private_ai_scope(user_id: str, db: Any = None) -> Iterator[PrivateContext]:
    context = PrivateContext(str(user_id), db)
    marker = _scope.set(context)
    try:
        yield context
    finally:
        _scope.reset(marker)


async def prepare_text(text: str) -> tuple[str, PrivateContext | None]:
    if len(text) > settings.AI_MAX_INPUT_CHARS:
        raise PrivacyBlocked("input_limit")
    if settings.AI_DATA_MODE == "paid_private":
        return text, None
    if settings.AI_DATA_MODE != "free_redacted":
        raise PrivacyBlocked("invalid_data_mode")
    context = _scope.get()
    if context is None:
        raise PrivacyBlocked("missing_user_scope")
    await context.load()
    return context.minimize(text), context
