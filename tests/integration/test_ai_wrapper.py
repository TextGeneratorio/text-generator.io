import pytest

pytestmark = [pytest.mark.integration, pytest.mark.internet]

from questions.ai_wrapper import generate_with_claude

@pytest.mark.asyncio
async def test_generate_with_claude():
    prompt = "What is the capital of France?"
    response = await generate_with_claude(prompt)

    assert response is not None
    assert isinstance(response, str)
    assert len(response) > 0
    assert "Paris" in response
