"""Optional hosted integrations stay closed until real acceptance is recorded."""
from app.core.config import settings
from app.core.errors import ConflictError


def optional_enabled(name):
    if not settings.requires_postgres():
        # Synthetic local development/tests retain existing regression coverage.
        return True
    return bool(getattr(settings, name))


def require_google_release():
    if not optional_enabled('GOOGLE_INTEGRATIONS_RELEASE_VERIFIED'):
        raise ConflictError('Google connections and synchronization are disabled for this release pending hosted acceptance. Existing connections can still be disconnected.')


def require_portfolio_release():
    if not optional_enabled('PORTFOLIO_PUBLISHING_RELEASE_VERIFIED'):
        raise ConflictError('Public portfolio sharing is disabled for this release pending hosted acceptance. Existing shares can still be revoked.')
