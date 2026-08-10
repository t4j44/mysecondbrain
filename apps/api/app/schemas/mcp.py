from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class MCPCredentialCreateRequest(BaseModel):
    client_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Name of external AI client (e.g., Claude Desktop, Gemini CLI)",
    )
    client_type: str = Field("stdio", description="Transport layer mode: stdio, sse, or plugin")
    scopes: List[str] = Field(
        default_factory=lambda: ["mcp:read"], description="Assigned granular scope permissions"
    )
    expires_at: Optional[str] = Field(None, description="Optional ISO 8601 expiration timestamp")


class MCPCredentialMeta(BaseModel):
    credential_id: str
    user_id: str
    client_name: str
    client_type: str
    scopes: List[str]
    key_prefix: str
    status: str
    created_at: str
    last_used_at: Optional[str] = None
    expires_at: Optional[str] = None
    revoked_at: Optional[str] = None


class MCPCredentialCreateResponse(MCPCredentialMeta):
    plaintext_key: str = Field(
        ..., description="Plaintext API secret key returned exactly ONCE upon creation or rotation"
    )


class MCPCredentialListResponse(BaseModel):
    data: List[MCPCredentialMeta]
    meta: Dict[str, Any]


class MCPCredentialSingleResponse(BaseModel):
    data: MCPCredentialMeta
    meta: Dict[str, Any]


class MCPCredentialSecretResponse(BaseModel):
    data: MCPCredentialCreateResponse
    meta: Dict[str, Any]
