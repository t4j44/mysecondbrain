import base64
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.core.errors import AIProviderError, RateLimitExceededError
from app.main import app

client = TestClient(app)

@pytest.fixture(autouse=True)
def signed_in_analysis_client(auth_headers):
    client.headers.update(auth_headers)
    yield
    client.headers.pop('Authorization', None)


def test_analysis_requires_authentication():
    response = client.post('/api/v1/analyze/pdf', json={}, headers={'Authorization': ''})
    assert response.status_code == 401


# Helper sample payloads
VALID_PDF_BYTES = b"%PDF-1.4 sample pdf content for testing regulatory compliance."
VALID_PDF_B64 = base64.b64encode(VALID_PDF_BYTES).decode("utf-8")

VALID_PNG_BYTES = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR sample png image data"
VALID_PNG_B64 = base64.b64encode(VALID_PNG_BYTES).decode("utf-8")


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


@patch("app.api.v1.endpoints.pdf_analysis.GoogleGenAIClient")
def test_valid_base64_pdf_analysis(mock_client_cls):
    # Setup mock Gemini client
    mock_instance = MagicMock()
    mock_instance.analyze_document_inline.return_value = {
        "analysis": "COMPLIANCE AUDIT: Document adheres to standard disclosures. Risk Level: LOW.",
        "model_used": "gemini-2.5-flash",
        "mime_type": "application/pdf",
        "bytes_processed": len(VALID_PDF_BYTES),
        "system_persona": "Strict Regulatory Compliance",
    }
    mock_client_cls.return_value = mock_instance

    payload = {
        "file_data": VALID_PDF_B64,
        "filename": "contract.pdf",
        "mime_type": "application/pdf",
        "prompt": "Check for GDPR compliance.",
    }

    response = client.post("/api/v1/analyze/pdf", json=payload)
    assert response.status_code == 200, response.text
    body = response.json()

    assert "data" in body
    assert "meta" in body
    assert body["data"]["filename"] == "contract.pdf"
    assert body["data"]["mime_type"] == "application/pdf"
    assert body["data"]["system_persona"] == "Strict Regulatory Compliance"
    assert "GDPR" in mock_instance.analyze_document_inline.call_args[1]["prompt"]
    assert "request_id" in body["meta"]


@patch("app.api.v1.endpoints.pdf_analysis.GoogleGenAIClient")
def test_valid_base64_image_analysis(mock_client_cls):
    mock_instance = MagicMock()
    mock_instance.analyze_document_inline.return_value = {
        "analysis": "IMAGE COMPLIANCE AUDIT: Clear safety labels verified. Risk Level: LOW.",
        "model_used": "gemini-2.5-flash",
        "mime_type": "image/png",
        "bytes_processed": len(VALID_PNG_BYTES),
        "system_persona": "Strict Regulatory Compliance",
    }
    mock_client_cls.return_value = mock_instance

    payload = {"file_data": VALID_PNG_B64, "filename": "safety_label.png", "mime_type": "image/png"}

    response = client.post("/api/v1/analyze/pdf", json=payload)
    assert response.status_code == 200
    body = response.json()

    assert body["data"]["filename"] == "safety_label.png"
    assert body["data"]["mime_type"] == "image/png"


def test_file_size_exceeded_error():
    # Mock settings max_size to 0.0001 MB (100 Bytes) to test limit trigger
    with patch("app.services.pdf_validator.settings.MAX_FILE_SIZE_MB", 0.00005):
        payload = {
            "file_data": VALID_PDF_B64,
            "filename": "large_file.pdf",
            "mime_type": "application/pdf",
        }

        response = client.post("/api/v1/analyze/pdf", json=payload)
        assert response.status_code == 413
        body = response.json()

        assert "error" in body
        assert body["error"]["code"] == "FILE_TOO_LARGE"
        assert "exceeds maximum allowed limit" in body["error"]["message"]
        assert "request_id" in body["error"]


def test_unsupported_media_type_error():
    payload = {
        "file_data": VALID_PDF_B64,
        "filename": "executable.exe",
        "mime_type": "application/x-msdownload",
    }

    response = client.post("/api/v1/analyze/pdf", json=payload)
    assert response.status_code == 415
    body = response.json()

    assert "error" in body
    assert body["error"]["code"] == "UNSUPPORTED_MEDIA_TYPE"
    assert "is not supported" in body["error"]["message"]


def test_invalid_corrupt_base64_error():
    payload = {
        "file_data": "---INVALID-BASE64-PAYLOAD---!!!",
        "filename": "corrupt.pdf",
        "mime_type": "application/pdf",
    }

    response = client.post("/api/v1/analyze/pdf", json=payload)
    assert response.status_code == 400
    body = response.json()

    assert "error" in body
    assert body["error"]["code"] == "INVALID_BASE64"
    assert "Corrupt or invalid base64" in body["error"]["message"]


@patch("app.api.v1.endpoints.pdf_analysis.GoogleGenAIClient")
def test_rate_limit_exceeded_handling(mock_client_cls):
    mock_instance = MagicMock()
    mock_instance.analyze_document_inline.side_effect = RateLimitExceededError(
        retry_after_seconds=60, message="Rate limit quota reached."
    )
    mock_client_cls.return_value = mock_instance

    payload = {"file_data": VALID_PDF_B64, "filename": "test.pdf", "mime_type": "application/pdf"}

    response = client.post("/api/v1/analyze/pdf", json=payload)
    assert response.status_code == 429
    assert response.headers.get("Retry-After") == "60"
    body = response.json()

    assert "error" in body
    assert body["error"]["code"] == "RATE_LIMIT_EXCEEDED"


@patch("app.api.v1.endpoints.pdf_analysis.GoogleGenAIClient")
def test_ai_provider_error_handling(mock_client_cls):
    mock_instance = MagicMock()
    mock_instance.analyze_document_inline.side_effect = AIProviderError(
        provider_message="Connection timed out to Google server.", provider="GoogleGenAI"
    )
    mock_client_cls.return_value = mock_instance

    payload = {"file_data": VALID_PDF_B64, "filename": "test.pdf", "mime_type": "application/pdf"}

    response = client.post("/api/v1/analyze/pdf", json=payload)
    assert response.status_code == 503
    body = response.json()

    assert "error" in body
    assert body["error"]["code"] == "AI_SERVICE_UNAVAILABLE"


@patch("app.api.v1.endpoints.pdf_analysis.GoogleGenAIClient")
def test_valid_binary_upload_analysis(mock_client_cls):
    mock_instance = MagicMock()
    mock_instance.analyze_document_inline.return_value = {
        "analysis": "COMPLIANCE AUDIT: Uploaded binary PDF adheres to required regulatory standards.",
        "model_used": "gemini-2.5-flash",
        "mime_type": "application/pdf",
        "bytes_processed": len(VALID_PDF_BYTES),
        "system_persona": "Strict Regulatory Compliance",
    }
    mock_client_cls.return_value = mock_instance

    files = {"file": ("contract_upload.pdf", VALID_PDF_BYTES, "application/pdf")}
    data = {"prompt": "Verify audit trail requirements."}

    response = client.post("/api/v1/analyze/upload", files=files, data=data)
    assert response.status_code == 200, response.text
    body = response.json()

    assert body["data"]["filename"] == "contract_upload.pdf"
    assert body["data"]["mime_type"] == "application/pdf"
    assert body["data"]["file_size_bytes"] == len(VALID_PDF_BYTES)
    assert (
        body["data"]["analysis"]
        == "COMPLIANCE AUDIT: Uploaded binary PDF adheres to required regulatory standards."
    )
