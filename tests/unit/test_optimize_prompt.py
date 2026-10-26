import pytest
from types import SimpleNamespace

from main import OptimizePromptParams, optimize_prompt

pytestmark = [pytest.mark.inference]


@pytest.mark.asyncio
async def test_optimize_prompt(monkeypatch):
    calls = []

    async def fake_query(prompt, schema, system_message=None, model=None, **kwargs):
        calls.append({"prompt": prompt, "model": model})
        if "Current Prompt" in prompt:
            # evolve
            data = {"prompt": prompt.split("\n")[-1] + " improved"}
        else:
            score = 10
            if "improved" in prompt:
                score = 90
            data = {"score": score, "feedback": "ok"}
        return SimpleNamespace(data=data, model="deepseek-chat", provider="deepseek")

    monkeypatch.setattr("main.query_tool_json_async", fake_query)
    params = OptimizePromptParams(prompt="start", evolve_prompt="evolve", judge_prompt="judge", iterations=2)
    result = await optimize_prompt(params)
    assert result["final_prompt"].endswith("improved")
    assert len(result["evaluations"]) == 3
    assert result["model"] == "deepseek-chat"
    assert all(call["model"] == "deepseek-chat" for call in calls)
