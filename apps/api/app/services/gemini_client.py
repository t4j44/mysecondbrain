import logging
from typing import Any, Dict, Optional

from app.config import settings
from app.core.errors import AIProviderError, RateLimitExceededError

logger = logging.getLogger("api.services.gemini")

STRICT_REGULATORY_COMPLIANCE_PERSONA = (
    "You are an expert Strict Regulatory Compliance AI Auditor. "
    "Your mandate is to rigorously analyze submitted documents (PDFs and images) against statutory regulations, "
    "privacy laws (GDPR, CCPA), financial rules (SOX, SEC, FINRA), health compliance (HIPAA), safety standards, "
    "and legal contractual norms.\n\n"
    "Guidelines:\n"
    "1. Thoroughly inspect all text, tables, headers, fine print, and embedded details.\n"
    "2. Identify specific compliance violations, missing mandatory disclosures, high-risk clauses, and legal ambiguities.\n"
    "3. Assign an explicit Compliance Risk Rating: LOW, MEDIUM, HIGH, or CRITICAL.\n"
    "4. Provide structured, actionable remediation steps for every identified issue.\n"
    "5. Maintain absolute objectivity, technical formality, and zero speculation."
)


class GoogleGenAIClient:
    """Wrapper around GoogleGenAI SDK supporting inline base64/bytes processing and strict personas."""

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model_name = model_name or settings.GEMINI_MODEL
        self._client = None

    def _get_client(self):
        """Lazy initialization of google.genai.Client."""
        from google import genai

        if not self.api_key or self.api_key == "placeholder_gemini_key":
            logger.warning("GEMINI_API_KEY is unset or using default placeholder.")
        return genai.Client(api_key=self.api_key)

    def analyze_document_inline(
        self,
        raw_bytes: bytes,
        mime_type: str,
        prompt: Optional[str] = None,
        custom_system_instruction: Optional[str] = None,
        temperature: float = 0.2,
    ) -> Dict[str, Any]:
        """
        Submits raw document/image bytes to GoogleGenAI inline payload endpoint.

        Args:
            raw_bytes (bytes): Decoded PDF or image content bytes.
            mime_type (str): MIME type (e.g. 'application/pdf', 'image/png').
            prompt (str, optional): Specific user query or standard prompt.
            custom_system_instruction (str, optional): Override default compliance persona.
            temperature (float): Generation temperature.

        Returns:
            Dict[str, Any]: Structured analysis response including content and metadata.
        """
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=self.api_key)

            system_persona = custom_system_instruction or STRICT_REGULATORY_COMPLIANCE_PERSONA

            # Build inline base64 Part
            part = types.Part.from_bytes(data=raw_bytes, mime_type=mime_type)

            default_user_prompt = (
                "Please perform a complete Strict Regulatory Compliance Audit on this document. "
                "Highlight key findings, compliance risks, missing disclosures, risk level, and required actions."
            )
            user_text = prompt or default_user_prompt

            config = types.GenerateContentConfig(
                system_instruction=system_persona,
                temperature=temperature,
            )

            content_parts: list[Any] = [part, user_text]
            response = client.models.generate_content(
                model=self.model_name, contents=content_parts, config=config
            )

            text_result = getattr(response, "text", "") or str(response)

            return {
                "analysis": text_result,
                "model_used": self.model_name,
                "mime_type": mime_type,
                "bytes_processed": len(raw_bytes),
                "system_persona": "Strict Regulatory Compliance",
            }

        except Exception as exc:
            exc_name = exc.__class__.__name__
            status_code = getattr(exc, "code", None)

            if status_code == 429 or "429" in str(exc) or "ResourceExhausted" in exc_name:
                logger.warning(f"GoogleGenAI rate limit exceeded: {exc}")
                raise RateLimitExceededError(
                    retry_after_seconds=60,
                    message="GoogleGenAI rate limit exceeded. Please retry after 60 seconds.",
                ) from exc

            logger.error(f"GoogleGenAI client execution error: {exc}", exc_info=True)
            raise AIProviderError(provider_message=str(exc), provider="GoogleGenAI") from exc
