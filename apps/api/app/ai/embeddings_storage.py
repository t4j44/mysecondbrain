"""Fail-closed helpers for embedding persistence (G0 Product Truth Gate)."""

import math
from typing import Any, List, Sequence

from app.core.errors import EmbeddingStorageNotImplementedError

EXPECTED_EMBEDDING_DIM = 768


def require_storable_embedding_vector(
    value: Any, *, dimensions: int = EXPECTED_EMBEDDING_DIM
) -> List[float]:
    """
    Accept only a full numeric vector suitable for real vector storage.

    Rejects truncated string dumps (e.g. ``str(vector[:10]) + "..."``), empty
    payloads, and wrong-dimension lists. Callers must not report embedding
    success unless this validation passes AND durable vector storage is wired.
    """
    if value is None:
        raise EmbeddingStorageNotImplementedError(
            details={"reason": "embedding_is_null"},
        )
    if isinstance(value, str):
        raise EmbeddingStorageNotImplementedError(
            message=(
                "String/truncated embedding payloads cannot be stored as real vectors."
            ),
            details={"reason": "embedding_is_string"},
        )
    if not isinstance(value, (list, tuple)):
        raise EmbeddingStorageNotImplementedError(
            details={"reason": "embedding_wrong_type", "type": type(value).__name__},
        )

    try:
        floats = [float(x) for x in value]
    except (TypeError, ValueError) as exc:
        raise EmbeddingStorageNotImplementedError(
            details={"reason": "embedding_non_numeric"},
        ) from exc

    if len(floats) != dimensions:
        raise EmbeddingStorageNotImplementedError(
            message=(
                f"Embedding dimension {len(floats)} is not a storable "
                f"{dimensions}-d vector; refusing truncated/fake success."
            ),
            details={
                "reason": "embedding_wrong_dimension",
                "actual_dim": len(floats),
                "expected_dim": dimensions,
            },
        )
    if any(isinstance(v, bool) for v in value) or not all(math.isfinite(v) for v in floats) or not any(floats):
        raise EmbeddingStorageNotImplementedError(details={"reason": "embedding_invalid_values"})
    return floats


def refuse_embedding_success_without_vector_storage(
    *, context: str = "document_processing"
) -> None:
    """Explicit G0 block: vector persistence success path is not implemented."""
    raise EmbeddingStorageNotImplementedError(
        details={"reason": "vector_storage_not_wired", "context": context},
    )


def looks_like_truncated_embedding_dump(value: Any) -> bool:
    """Heuristic used by regression tests against the historical false-success pattern."""
    if not isinstance(value, str):
        return False
    stripped = value.strip()
    return stripped.endswith("...") and ("[" in stripped or stripped.startswith("("))


def assert_not_truncated_embedding_sequence(values: Sequence[Any]) -> None:
    for item in values:
        if looks_like_truncated_embedding_dump(item):
            raise EmbeddingStorageNotImplementedError(
                details={"reason": "truncated_embedding_dump_detected"},
            )
