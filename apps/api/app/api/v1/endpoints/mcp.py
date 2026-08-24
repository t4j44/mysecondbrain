"""
MCP Credential Management FastAPI Router
Module Owner: Agent 10 — Secure MCP Server and External AI Access Agent
Endpoints: /api/v1/mcp/credentials
"""

from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import AuthenticatedUser, get_current_user
from app.dependencies.database import get_db_session
from app.schemas.mcp import (
    MCPCredentialCreateRequest,
    MCPCredentialCreateResponse,
    MCPCredentialListResponse,
    MCPCredentialMeta,
    MCPCredentialSecretResponse,
    MCPCredentialSingleResponse,
)
from app.services.mcp import MCPCredentialService

router = APIRouter(prefix="/credentials", tags=["mcp-credentials"])
service = MCPCredentialService()


def build_meta(request_id: str = "N/A") -> Dict[str, Any]:
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "api_version": "v1",
        "module": "mcp-server",
        "request_id": request_id,
    }


@router.get("", response_model=MCPCredentialListResponse, summary="List MCP credentials")
async def list_credentials(
    request: Request,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> MCPCredentialListResponse:
    creds = await service.list_credentials(db, user_id=current_user.id)
    req_id = getattr(request.state, "request_id", "N/A")
    return MCPCredentialListResponse(
        data=[MCPCredentialMeta.model_validate(c) for c in creds],
        meta=build_meta(req_id),
    )


@router.post(
    "",
    response_model=MCPCredentialSecretResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new MCP credential",
)
async def create_credential(
    body: MCPCredentialCreateRequest,
    request: Request,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> MCPCredentialSecretResponse:
    req_id = getattr(request.state, "request_id", "N/A")
    cred = await service.create_credential(db, user_id=current_user.id, req=body, request_id=req_id)
    await db.commit()
    return MCPCredentialSecretResponse(
        data=MCPCredentialCreateResponse.model_validate(cred),
        meta=build_meta(req_id),
    )


@router.get(
    "/{credential_id}", response_model=MCPCredentialSingleResponse, summary="Get credential details"
)
async def get_credential(
    credential_id: str,
    request: Request,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> MCPCredentialSingleResponse:
    cred = await service.get_credential(db, user_id=current_user.id, credential_id=credential_id)
    if not cred:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Requested MCP credential was not found in your workspace.",
        )
    req_id = getattr(request.state, "request_id", "N/A")
    return MCPCredentialSingleResponse(
        data=MCPCredentialMeta.model_validate(cred),
        meta=build_meta(req_id),
    )


@router.post(
    "/{credential_id}/rotate",
    response_model=MCPCredentialSecretResponse,
    summary="Rotate MCP credential key",
)
async def rotate_credential(
    credential_id: str,
    request: Request,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> MCPCredentialSecretResponse:
    req_id = getattr(request.state, "request_id", "N/A")
    cred = await service.rotate_credential(
        db, user_id=current_user.id, credential_id=credential_id, request_id=req_id
    )
    if not cred:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Requested MCP credential was not found in your workspace.",
        )
    await db.commit()
    return MCPCredentialSecretResponse(
        data=MCPCredentialCreateResponse.model_validate(cred),
        meta=build_meta(req_id),
    )


@router.post(
    "/{credential_id}/revoke",
    response_model=MCPCredentialSingleResponse,
    summary="Revoke MCP credential key",
)
async def revoke_credential(
    credential_id: str,
    request: Request,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> MCPCredentialSingleResponse:
    req_id = getattr(request.state, "request_id", "N/A")
    cred = await service.revoke_credential(
        db, user_id=current_user.id, credential_id=credential_id, request_id=req_id
    )
    if not cred:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Requested MCP credential was not found in your workspace.",
        )
    await db.commit()
    return MCPCredentialSingleResponse(
        data=MCPCredentialMeta.model_validate(cred),
        meta=build_meta(req_id),
    )


@router.delete(
    "/{credential_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete MCP credential record",
)
async def delete_credential(
    credential_id: str,
    request: Request,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    req_id = getattr(request.state, "request_id", "N/A")
    success = await service.delete_credential(
        db, user_id=current_user.id, credential_id=credential_id, request_id=req_id
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Requested MCP credential was not found in your workspace.",
        )
    await db.commit()
