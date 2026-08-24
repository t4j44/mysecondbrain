import hashlib
import math
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

import httpx

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


def _deterministic_pseudo_embedding(text: str, dimensions: int = 768) -> List[float]:
    """
    Generates a normalized, deterministic 768-dimension vector from text content.
    Used strictly as a dev/unit-test fallback when offline without live Gemini API keys.
    """
    if not text:
        return [0.0] * dimensions

    # Use multi-seed SHA-256 rolling hashes to produce 768 deterministic float values
    raw_values: List[float] = []
    text_bytes = text.encode("utf-8")
    for block in range((dimensions + 7) // 8):
        block_seed = f"{block}:{len(text)}:".encode("utf-8") + text_bytes
        h = hashlib.sha256(block_seed).digest()
        for i in range(0, len(h), 4):
            if len(raw_values) >= dimensions:
                break
            val = int.from_bytes(h[i : i + 4], byteorder="big", signed=True) / (2**31)
            raw_values.append(val)

    # Normalize to unit length
    norm = math.sqrt(sum(x * x for x in raw_values)) or 1.0
    return [round(x / norm, 6) for x in raw_values]


class GeminiLLMProvider(BaseLLMProvider):
    """
    Official Google Gemini AI provider for Second Brain LLM synthesis & embeddings.
    Integrates Gemini 2.5 Flash and text-embedding-004.
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
            if settings.is_production():
                raise AIProviderError(
                    message="Gemini API key is unconfigured in production environment.",
                    code=ErrorCode.AI_PROVIDER_NOT_CONFIGURED,
                )
            # Safe deterministic generation for local development and offline automated test runs
            grounded_snippet = prompt[:120].replace("\n", " ")
            return (
                f"[Grounded Synthesis based on Taj's Second Brain]\n"
                f"Regarding: {grounded_snippet}\n"
                f"The verified evidence from canonical records indicates clear strategic alignment and execution progress."
            )

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
                payload: Dict[str, Any] = {"contents": [{"parts": [{"text": prompt}]}]}
                if system_instruction:
                    payload["system_instruction"] = {"parts": [{"text": system_instruction}]}
                response = await client.post(url, json=payload)

                if response.status_code == 429:
                    raise AIProviderError(
                        message="Gemini API rate limit or quota exceeded.",
                        code=ErrorCode.AI_PROVIDER_ERROR,
                        details={"status_code": 429, "provider": "gemini"},
                    )

                response.raise_for_status()
                data = response.json()
                return data["candidates"][0]["content"]["parts"][0]["text"]
        except AIProviderError:
            raise
        except httpx.HTTPStatusError as e:
            logger.error(f"Gemini API HTTP error {e.response.status_code}: {e.response.text}")
            raise AIProviderError(
                message=f"Gemini model generation failed with status {e.response.status_code}.",
                code=ErrorCode.AI_PROVIDER_ERROR,
                details={"status_code": e.response.status_code, "error": str(e)},
            ) from e
        except Exception as e:
            logger.error(f"Gemini API request failed: {str(e)}")
            raise AIProviderError(
                message="Gemini model generation failed.",
                code=ErrorCode.AI_PROVIDER_ERROR,
                details={"provider": "gemini", "error": str(e)},
            ) from e

    async def embed_text(self, text: str) -> List[float]:
        """
        Generate complete 768-dimensional numeric embedding vector.
        Never truncates or returns synthetic vectors in production.
        """
        if self._is_unconfigured():
            if settings.is_production():
                raise AIProviderError(
                    message="Gemini embedding API key is unconfigured in production environment.",
                    code=ErrorCode.AI_PROVIDER_NOT_CONFIGURED,
                )
            # Offline / local development deterministic 768-dim normalized embedding
            return _deterministic_pseudo_embedding(text, dimensions=768)

        try:
            clean_text = text[:8000].strip()
            if not clean_text:
                return [0.0] * 768

            async with httpx.AsyncClient(timeout=15.0) as client:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.embedding_model}:embedContent?key={self.api_key}"
                response = await client.post(
                    url, json={"content": {"parts": [{"text": clean_text}]}}
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
                return [float(v) for v in values]
        except AIProviderError:
            raise
        except Exception as e:
            logger.error(f"Gemini embedding failed: {str(e)}")
            raise AIProviderError(
                "Failed to generate embedding vector.",
                code=ErrorCode.AI_PROVIDER_ERROR,
                details={"provider": "gemini", "error": str(e)},
            ) from e


def get_llm_provider(prefer_provider: str = "gemini") -> BaseLLMProvider:
    """Factory delivering the primary Gemini AI provider for Taj's Second Brain."""
    return GeminiLLMProvider()
