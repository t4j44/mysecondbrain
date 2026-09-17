import math
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

import httpx

from app.ai.privacy import prepare_text
from app.core.config import settings
from app.core.constants import ErrorCode
from app.core.errors import AIProviderError
from app.core.logging import logger


class BaseLLMProvider(ABC):
    @abstractmethod
    async def generate_content(
        self, prompt: str, system_instruction: Optional[str] = None, **kwargs: Any
    ) -> str:
        pass

    @abstractmethod
    async def embed_text(self, text: str) -> List[float]:
        pass


class GeminiLLMProvider(BaseLLMProvider):
    """
    Official Google Gemini AI provider for Second Brain LLM synthesis & embeddings.
    Uses configurable Gemini generation and embedding models.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = settings.GEMINI_MODEL,
        embedding_model: str = settings.GEMINI_EMBEDDING_MODEL,
    ):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model = model
        self.embedding_model = embedding_model
        self.provider_name = "google_gemini"

    def _is_unconfigured(self) -> bool:
        """Treat missing / placeholder / CI mock keys as offline (fail-closed in production)."""
        if not self.api_key:
            return True
        key = self.api_key.lower()
        markers = (
            "placeholder",
            "mock",
            "your-",
            "changeme",
            "test_only",
            "for_testing",
            "for_local",
        )
        return any(marker in key for marker in markers)

    async def generate_content(
        self, prompt: str, system_instruction: Optional[str] = None, **kwargs: Any
    ) -> str:
        if self._is_unconfigured():
            raise AIProviderError(
                message="Gemini is not configured. Your saved records remain available.",
                code=ErrorCode.AI_PROVIDER_NOT_CONFIGURED,
            )

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                minimized, privacy = await prepare_text(prompt)
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
                payload: Dict[str, Any] = {"contents": [{"parts": [{"text": minimized}]}],
                    "generationConfig": {"maxOutputTokens": settings.AI_MAX_OUTPUT_TOKENS}}
                if system_instruction:
                    payload["system_instruction"] = {"parts": [{"text": system_instruction}]}
                response = await client.post(url, json=payload, headers={"x-goog-api-key": self.api_key})

                if response.status_code == 429:
                    raise AIProviderError(
                        message="Gemini API rate limit or quota exceeded.",
                        code=ErrorCode.AI_PROVIDER_ERROR,
                        details={"status_code": 429, "provider": "gemini"},
                    )

                response.raise_for_status()
                data = response.json()
                result = data["candidates"][0]["content"]["parts"][0]["text"]
                return privacy.restore(result) if privacy else result
        except AIProviderError:
            raise
        except httpx.HTTPStatusError as e:
            logger.error("Gemini API HTTP error %s", e.response.status_code)
            raise AIProviderError(
                message=f"Gemini model generation failed with status {e.response.status_code}.",
                code=ErrorCode.AI_PROVIDER_ERROR,
                details={"status_code": e.response.status_code},
            ) from e
        except Exception as e:
            from app.ai.privacy import PrivacyBlocked
            if isinstance(e, PrivacyBlocked):
                raise
            logger.error("Gemini API request failed (%s)", type(e).__name__)
            raise AIProviderError(
                message="Gemini model generation failed.",
                code=ErrorCode.AI_PROVIDER_ERROR,
                details={"provider": "gemini"},
            ) from e

    async def embed_text(self, text: str, task_type: str = "RETRIEVAL_DOCUMENT") -> List[float]:
        """
        Generate complete 768-dimensional numeric embedding vector.
        Never truncates or returns synthetic vectors in production.
        """
        if self._is_unconfigured():
            raise AIProviderError(
                message="Gemini embeddings are not configured.",
                code=ErrorCode.AI_PROVIDER_NOT_CONFIGURED,
            )

        try:
            clean_text, _privacy = await prepare_text(text)
            clean_text = clean_text.strip()
            if not clean_text:
                return [0.0] * 768

            async with httpx.AsyncClient(timeout=15.0) as client:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.embedding_model}:embedContent"
                response = await client.post(
                    url, headers={"x-goog-api-key": self.api_key},
                    json={"content": {"parts": [{"text": clean_text}]},
                          "taskType": task_type, "outputDimensionality": 768}
                )

                if response.status_code == 429:
                    raise AIProviderError(
                        message="Gemini embedding rate limit exceeded.",
                        code=ErrorCode.AI_PROVIDER_ERROR,
                        details={"status_code": 429},
                    )

                response.raise_for_status()
                data = response.json()
                values = data.get("embedding", {}).get("values", [])
                if not values:
                    raise ValueError("Gemini returned empty embedding vector.")
                from app.ai.embeddings_storage import require_storable_embedding_vector
                vector = require_storable_embedding_vector(values)
                magnitude = math.sqrt(sum(v * v for v in vector))
                if not magnitude or not math.isfinite(magnitude):
                    raise ValueError("Invalid embedding vector")
                return [v / magnitude for v in vector]
        except AIProviderError:
            raise
        except Exception as e:
            from app.ai.privacy import PrivacyBlocked
            if isinstance(e, PrivacyBlocked):
                raise
            logger.error("Gemini embedding failed (%s)", type(e).__name__)
            raise AIProviderError(
                "Failed to generate embedding vector.",
                code=ErrorCode.AI_PROVIDER_ERROR,
                details={"provider": "gemini"},
            ) from e


def get_llm_provider(prefer_provider: str = "gemini") -> BaseLLMProvider:
    """Factory delivering the primary Gemini AI provider for Taj's Second Brain."""
    return GeminiLLMProvider()
