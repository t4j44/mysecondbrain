import base64
import time
import uuid
from typing import Any, Dict, Optional

from fastapi import APIRouter, File, Form, Request, UploadFile, status
from pydantic import BaseModel, Field

from app.config import settings
from app.core.errors import InvalidPayloadError
from app.services.gemini_client import GoogleGenAIClient
from app.services.pdf_validator import PDFValidator

router = APIRouter(prefix="/analyze", tags=["PDF & Document Analysis"])


class PDFAnalysisRequest(BaseModel):
    file_data: str = Field(..., description="Base64 encoded PDF or image data string")
    filename: Optional[str] = Field(default="document.pdf", description="Original filename")
    mime_type: Optional[str] = Field(default="application/pdf", description="Declared MIME type")
    prompt: Optional[str] = Field(default=None, description="Optional custom user audit prompt")
    system_persona_override: Optional[str] = Field(
        default=None, description="Optional system persona override"
    )


class PDFAnalysisData(BaseModel):
    filename: str
    mime_type: str
    file_size_bytes: int
    analysis: str
    model_used: str
    system_persona: str


class PDFAnalysisSuccessResponse(BaseModel):
    data: PDFAnalysisData
    meta: Dict[str, Any]


@router.post(
    "/pdf",
    response_model=PDFAnalysisSuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze PDF or Image Document for Regulatory Compliance",
)
async def analyze_pdf_base64(
    payload: PDFAnalysisRequest, request: Request
) -> PDFAnalysisSuccessResponse:
    """
    Accepts base64-encoded PDF or image content, validates size & integrity,
    and runs it through GoogleGenAI using a Strict Regulatory Compliance persona.
    """
    req_id = getattr(request.state, "request_id", f"req_{uuid.uuid4().hex[:10]}")

    raw_bytes, verified_mime = PDFValidator.decode_and_validate(
        file_data_b64=payload.file_data,
        declared_mime_type=payload.mime_type or "application/pdf",
        max_size_mb=settings.MAX_FILE_SIZE_MB,
    )

    gemini_client = GoogleGenAIClient()
    analysis_result = gemini_client.analyze_document_inline(
        raw_bytes=raw_bytes,
        mime_type=verified_mime,
        prompt=payload.prompt,
        custom_system_instruction=payload.system_persona_override,
    )

    return PDFAnalysisSuccessResponse(
        data=PDFAnalysisData(
            filename=payload.filename or "document.pdf",
            mime_type=verified_mime,
            file_size_bytes=len(raw_bytes),
            analysis=analysis_result["analysis"],
            model_used=analysis_result["model_used"],
            system_persona=analysis_result["system_persona"],
        ),
        meta={
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "request_id": req_id,
        },
    )


@router.post(
    "/upload",
    response_model=PDFAnalysisSuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Upload binary PDF/Image file for Regulatory Compliance Analysis",
)
async def analyze_pdf_upload(
    request: Request,
    file: UploadFile = File(...),
    prompt: Optional[str] = Form(default=None),
) -> PDFAnalysisSuccessResponse:
    """
    Accepts multipart binary file upload, converts to bytes, validates size & format,
    and executes GoogleGenAI compliance analysis.
    """
    req_id = getattr(request.state, "request_id", f"req_{uuid.uuid4().hex[:10]}")

    content = await file.read()
    if not content:
        raise InvalidPayloadError("Uploaded file is empty (0 bytes)")

    b64_str = base64.b64encode(content).decode("utf-8")

    raw_bytes, verified_mime = PDFValidator.decode_and_validate(
        file_data_b64=b64_str,
        declared_mime_type=file.content_type or "application/pdf",
        max_size_mb=settings.MAX_FILE_SIZE_MB,
    )

    gemini_client = GoogleGenAIClient()
    analysis_result = gemini_client.analyze_document_inline(
        raw_bytes=raw_bytes, mime_type=verified_mime, prompt=prompt
    )

    return PDFAnalysisSuccessResponse(
        data=PDFAnalysisData(
            filename=file.filename or "uploaded_document.pdf",
            mime_type=verified_mime,
            file_size_bytes=len(raw_bytes),
            analysis=analysis_result["analysis"],
            model_used=analysis_result["model_used"],
            system_persona=analysis_result["system_persona"],
        ),
        meta={
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "request_id": req_id,
        },
    )
