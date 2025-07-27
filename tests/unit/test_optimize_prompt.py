import pytest
from main import OptimizePromptParams, optimize_prompt

pytestmark = [pytest.mark.inference]

@pytest.mark.asyncio
async def test_optimize_prompt(monkeypatch):
    async def fake_query(prompt, schema, system_message=None, model=None):
        if 'Current Prompt' in prompt:
            # evolve
            return {'prompt': prompt.split('\n')[-1] + ' improved'}
        else:
            score = 0.1
            if 'improved' in prompt:
                score = 0.9
            return {'score': score, 'feedback': 'ok'}
    monkeypatch.setattr('main.query_to_claude_json_async', fake_query)
    params = OptimizePromptParams(prompt='start', evolve_prompt='evolve', judge_prompt='judge', iterations=2)
    result = await optimize_prompt(params)
    assert result['final_prompt'].endswith('improved')
    assert len(result['evaluations']) == 3
