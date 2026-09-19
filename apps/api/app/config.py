import re
from typing import List, Literal

from pydantic import AliasChoices, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Environments that must never use SQLite (G1 ONE SCHEMA).
_POSTGRES_REQUIRED_ENVIRONMENTS = frozenset(
    {"integration", "e2e", "staging", "production"}
)


def _is_sqlite_url(url: str) -> bool:
    normalized = (url or "").strip().lower()
    return normalized.startswith("sqlite:") or "+aiosqlite" in normalized


class Settings(BaseSettings):
    APP_NAME: str = "Taj's Second Brain API"
    APP_VERSION: str = "1.0.0"
    RELEASE_SHA: str = Field(default='', validation_alias=AliasChoices('RELEASE_SHA', 'RENDER_GIT_COMMIT'))
    API_V1_PREFIX: str = "/api/v1"
    APP_ENV: str = "development"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    # Prefer PostgreSQL (supabase/migrations). SQLite is allowed only for isolated unit tests
    # (ENVIRONMENT/APP_ENV = test|development with explicit sqlite URL). Never for
    # integration/e2e/staging/production.
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@127.0.0.1:54322/postgres"

    # When true (default), startup verifies the migrated schema and never creates tables.
    DATABASE_SCHEMA_VERIFY: bool = True

    # Separate development/staging PostgreSQL (never production) used by the migration
    # bootstrap and the postgres integration suite. Empty = postgres integration BLOCKED.
    POSTGRES_TEST_DATABASE_URL: str = ""

    # Security & Encryption Credentials
    JWT_SECRET: str = "placeholder_jwt_secret_key_at_least_32_chars_long_for_testing"
    SUPABASE_JWT_SECRET: str = ""  # Temporary migration / local test fallback for legacy HS256 tokens
    JWT_ALGORITHM: str = "HS256"
    TOKEN_ENCRYPTION_KEY: str = "tajs_second_brain_secure_master_token_key_for_dev_and_tests"

    # AI Provider Configuration
    GEMINI_API_KEY: str = "placeholder_gemini_key"
    GEMINI_MODEL: str = "gemini-2.5-flash"
    GEMINI_EMBEDDING_MODEL: str = "gemini-embedding-001"
    # Billing is configured in Google Cloud; changing tiers never changes data ownership.
    AI_DATA_MODE: Literal["free_redacted", "paid_private"] = "free_redacted"
    AI_MAX_INPUT_CHARS: int = 24000
    AI_MAX_OUTPUT_TOKENS: int = 2048
    RAG_TOP_K: int = 6
    RAG_CONTEXT_MAX_CHARS: int = 12000
    RAG_NEIGHBOR_WINDOW: int = 1
    AI_EMBEDDING_DIMENSIONS: Literal[768] = 768
    JOB_WORKER_ENABLED: bool = True
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:3000/settings/integrations/google/callback"
    OPENAI_API_KEY: str = "placeholder_openai_key"
    OPENAI_MODEL: str = "gpt-4o"

    # Supabase Integration & Storage
    SUPABASE_URL: str = ""
    SUPABASE_SECRET_KEY: str = ""  # Primary modern server secret key (sb_secret_...)
    SUPABASE_SERVICE_ROLE_KEY: str = ""  # Backward-compatible legacy fallback key
    SUPABASE_JWKS_URL: str = ""  # Optional JWKS URL override
    STORAGE_BUCKET_DOCUMENTS: str = "brain-documents"
    FRONTEND_URL: str = "http://localhost:3000"
    MAX_FILE_SIZE_MB: int = 50
    MAX_FILE_SIZE_BYTES: int = 50 * 1024 * 1024

    # CORS & Network Headers
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    CORS_ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # MCP Streamable HTTP resource-server configuration
    MCP_ISSUER_URL: str = "http://localhost:8000"
    MCP_RESOURCE_SERVER_URL: str = "http://localhost:8000/mcp"
    MCP_ALLOWED_HOSTS: List[str] = [
        "localhost",
        "localhost:*",
        "127.0.0.1",
        "127.0.0.1:*",
        "testserver",
        "testserver:*",
    ]

    @property
    def supabase_secret(self) -> str:
        """Returns the primary modern secret key (sb_secret_...) or legacy service_role key fallback."""
        return self.SUPABASE_SECRET_KEY or self.SUPABASE_SERVICE_ROLE_KEY

    @property
    def supabase_jwks_url(self) -> str:
        """Returns configured JWKS URL or auto-derives from SUPABASE_URL."""
        if self.SUPABASE_JWKS_URL:
            return self.SUPABASE_JWKS_URL
        if self.SUPABASE_URL:
            return f"{self.SUPABASE_URL.rstrip('/')}/auth/v1/.well-known/jwks.json"
        return ""

    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production" or self.APP_ENV.lower() == "production"

    @property
    def verified_release_sha(self) -> str | None:
        """Only expose a full Git identifier, never arbitrary deployment environment text."""
        return self.RELEASE_SHA.lower() if re.fullmatch(r'[a-fA-F0-9]{40}', self.RELEASE_SHA) else None

    def uses_sqlite(self) -> bool:
        return _is_sqlite_url(self.DATABASE_URL)

    def requires_postgres(self) -> bool:
        """True when the active environment forbids SQLite (integration/e2e/staging/production)."""
        names = {self.ENVIRONMENT.lower().strip(), self.APP_ENV.lower().strip()}
        return bool(names & _POSTGRES_REQUIRED_ENVIRONMENTS)

    @model_validator(mode="after")
    def validate_production_configuration(self) -> "Settings":
        if not self.is_production():
            return self

        required_secrets = {
            "SUPABASE_URL": self.SUPABASE_URL,
            "TOKEN_ENCRYPTION_KEY": self.TOKEN_ENCRYPTION_KEY,
        }
        invalid = [
            name
            for name, value in required_secrets.items()
            if not value or value.lower().startswith(("placeholder", "your-", "tajs_second_brain"))
        ]
        secret = self.supabase_secret
        if not secret or secret.lower().startswith(("placeholder", "your-", "tajs_second_brain")):
            invalid.append("SUPABASE_SECRET_KEY (or SUPABASE_SERVICE_ROLE_KEY)")

        if invalid:
            raise ValueError(
                "Production configuration is missing real values for: " + ", ".join(invalid)
            )
        if not self.DATABASE_URL.startswith(("postgresql+asyncpg://", "postgresql://")):
            raise ValueError("Production DATABASE_URL must point to PostgreSQL.")
        mcp_urls = (self.MCP_ISSUER_URL, self.MCP_RESOURCE_SERVER_URL)
        if any("localhost" in url or "127.0.0.1" in url for url in mcp_urls):
            raise ValueError("Production MCP URLs must use the public Render URL.")
        return self

    @model_validator(mode="after")
    def validate_database_dialect(self) -> "Settings":
        """Fail fast when a non-unit-test environment is pointed at SQLite (G1 ONE SCHEMA)."""
        if self.requires_postgres() and self.uses_sqlite():
            raise ValueError(
                "SQLite is forbidden for "
                + "/".join(sorted(_POSTGRES_REQUIRED_ENVIRONMENTS))
                + " environments. supabase/migrations is the canonical schema; set DATABASE_URL "
                "to a migrated PostgreSQL database (postgresql+asyncpg://...)."
            )
        return self

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
