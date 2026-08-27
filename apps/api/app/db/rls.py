"""
Transaction-local Row Level Security identity for direct PostgreSQL connections (G2).

Supabase evaluates `auth.uid()` / `auth.jwt()` from the `request.jwt.claims` GUC and writes
its policies against the `authenticated` role. This module builds the exact statements that
inject a verified caller identity into a transaction.

Two invariants are non-negotiable:

1. **Transaction-local only.** Every statement uses `set_config(..., is_local => true)`
   (the function form of `SET LOCAL`), so identity dies with the transaction and can never
   leak to the next borrower of a pooled connection.
2. **Claims are derived from a verified JWT, never from client input.** Only the token
   subject, role and email are forwarded; arbitrary claims are not smuggled into the GUC.

Setting names are module constants; caller-supplied values are always bound parameters, so
there is no SQL string interpolation of identity data.
"""

from __future__ import annotations

import json
from typing import Any, Dict, Optional, Tuple
from uuid import UUID

# RLS policies are written for this role. It is never the connection/owner role, because a
# table owner bypasses RLS entirely.
RLS_ROLE = "authenticated"
ANON_ROLE = "anon"
_ALLOWED_RLS_ROLES = frozenset({RLS_ROLE, ANON_ROLE})

CLAIMS_SETTING = "request.jwt.claims"
SUBJECT_SETTING = "request.jwt.claim.sub"
ROLE_SETTING = "role"

# Read-only diagnostic used by the RLS tests to assert the active identity of a transaction.
IDENTITY_PROBE_SQL = (
    "SELECT current_user AS db_user, "
    f"current_setting('{CLAIMS_SETTING}', true) AS claims, "
    f"current_setting('{SUBJECT_SETTING}', true) AS subject"
)

IdentityStatements = Tuple[Tuple[str, Dict[str, str]], ...]


class RLSIdentityError(ValueError):
    """Raised when a caller identity cannot be represented safely as an RLS identity."""


def normalize_user_id(user_id: str) -> str:
    """Return the canonical UUID string for a verified JWT subject, or fail closed."""
    try:
        return str(UUID(str(user_id)))
    except (AttributeError, TypeError, ValueError) as exc:
        raise RLSIdentityError(
            "RLS identity requires a UUID subject from the verified JWT (sub claim)."
        ) from exc


def build_jwt_claims(
    user_id: str, *, email: Optional[str] = None, role: str = RLS_ROLE
) -> Dict[str, Any]:
    """Build the minimal Supabase-compatible claim set that auth.uid()/auth.jwt() read."""
    claims: Dict[str, Any] = {
        "sub": normalize_user_id(user_id),
        "role": role,
        "aud": role,
    }
    if email:
        claims["email"] = email
    return claims


def identity_statements(
    user_id: str, *, email: Optional[str] = None, role: str = RLS_ROLE
) -> IdentityStatements:
    """
    Return the ordered (sql, params) pairs that make a transaction run as `user_id`.

    Claims are set before the role switch so the role change cannot block the injection.
    """
    if role not in _ALLOWED_RLS_ROLES:
        raise RLSIdentityError(
            f"Refusing to switch to role '{role}'. Allowed RLS roles: "
            + ", ".join(sorted(_ALLOWED_RLS_ROLES))
        )

    normalized = normalize_user_id(user_id)
    claims = build_jwt_claims(normalized, email=email, role=role)
    payload = json.dumps(claims, separators=(",", ":"), sort_keys=True)

    return (
        (f"SELECT set_config('{CLAIMS_SETTING}', :claims, true)", {"claims": payload}),
        (f"SELECT set_config('{SUBJECT_SETTING}', :subject, true)", {"subject": normalized}),
        (f"SELECT set_config('{ROLE_SETTING}', :role, true)", {"role": role}),
    )
