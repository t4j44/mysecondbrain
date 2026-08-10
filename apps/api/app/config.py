from typing import List

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Taj's Second Brain API"
    APP_VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"
    APP_ENV: str = "development"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    # Database Configuration (Async SQLite default for effortless testing & self-contained development)
    DATABASE_URL: str = "sqlite+aiosqlite:///./brain_dev.db"

    # Security & Encryption Credentials
    JWT_SECRET: str = "placeholder_jwt_secret_key_at_least_32_chars_long_for_testing"
    SUPABASE_JWT_SECRET: str = "placeholder_jwt_secret_key_at_least_32_chars_long_for_testing"
    JWT_ALGORITHM: str = "HS256"
    TOKEN_ENCRYPTION_KEY: str = "tajs_second_brain_secure_master_token_key_for_dev_and_tests"

    # AI Provider Configuration
    GEMINI_API_KEY: str = "placeholder_gemini_key"
    GEMINI_MODEL: str = "gemini-2.5-flash"
    GEMINI_EMBEDDING_MODEL: str = "text-embedding-004"
    OPENAI_API_KEY: str = "placeholder_openai_key"
    OPENAI_MODEL: str = "gpt-4o"

    # Storage & Integrations
    SUPABASE_URL: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""
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

    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production" or self.APP_ENV.lower() == "production"

    @model_validator(mode="after")
    def validate_production_configuration(self) -> "Settings":
        if not self.is_production():
            return self

        required_secrets = {
            "SUPABASE_URL": self.SUPABASE_URL,
            "SUPABASE_SERVICE_ROLE_KEY": self.SUPABASE_SERVICE_ROLE_KEY,
            "SUPABASE_JWT_SECRET": self.SUPABASE_JWT_SECRET,
            "TOKEN_ENCRYPTION_KEY": self.TOKEN_ENCRYPTION_KEY,
        }
        invalid = [
            name
            for name, value in required_secrets.items()
            if not value or value.lower().startswith(("placeholder", "your-", "tajs_second_brain"))
        ]
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

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
