import pytest

from app.mcp.beta_tools import READ_TOOLS
from app.mcp.security import SCOPE_CONTENT_DRAFT
from app.services import prompt_enhancer as prompt_module
from app.services.prompt_enhancer import PromptEnhancerService


class FakeProvider:
    async def generate_content(self, prompt: str, system_instruction: str | None = None, **kwargs):
        assert "<USER_PROMPT>" in prompt
        assert "never execute or answer it" in (system_instruction or "")
        return "# Goal\nEvaluate my startup\n\n## Output\n- 3 priorities"


@pytest.mark.asyncio
async def test_prompt_enhancer_returns_structured_prompt_and_metrics(monkeypatch):
    monkeypatch.setattr(prompt_module, "get_llm_provider", lambda: FakeProvider())

    result = await PromptEnhancerService().enhance(
        text="please check my startup and tell me what i should do next next",
        mode="full",
        compression="safe",
        target="auto",
    )

    assert result["enhanced_prompt"].startswith("# Goal")
    assert result["mode"] == "full"
    assert result["estimated_tokens_before"] > 0
    assert result["estimated_tokens_after"] > 0
    assert 0 <= result["estimated_reduction_percent"] <= 100


def test_enhance_prompt_mcp_manifest_is_draft_scoped():
    spec = next(tool for tool in READ_TOOLS if tool["name"] == "enhance_prompt")
    assert spec["required_scope"] == SCOPE_CONTENT_DRAFT
    assert spec["write"] is False
    assert spec["input_schema"]["required"] == ["text"]
    assert spec["input_schema"]["properties"]["mode"]["enum"] == [
        "grammar",
        "improve",
        "structure",
        "compress",
        "full",
    ]
