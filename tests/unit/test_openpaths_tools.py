import pytest

from questions import openpaths_tools as op
from questions.tool_fixtures import tools_fixtures


class Resp:
    def __init__(self, data, ok=True, status_code=200):
        self._d, self.ok, self.status_code = data, ok, status_code

    def json(self):
        return self._d


class Session:
    def __init__(self, resp):
        self.resp, self.calls = resp, []

    def post(self, url, **kw):
        self.calls.append((url, kw))
        return self.resp

    get = post


@pytest.fixture(autouse=True)
def key(monkeypatch):
    monkeypatch.setenv("OPENPATHS_API_KEY", "k")


def test_credits_apply_markup_and_minimum():
    assert op.credits_for_usd(0.003) == 1
    assert op.credits_for_usd(0.04) == 7  # 0.04 * 1.6 = 6.4 cents -> 7
    assert op.video_credits(op.video_model("wan-3.0-text-to-video"), 5) == 40


def test_catalog_ids_unique_and_tools_registered():
    ids = [m.id for m in op.IMAGE_MODELS + op.VIDEO_MODELS]
    assert len(ids) == len(set(ids))
    for slug in [*op.LLM_TOOLS, "ai-image-studio", "ai-video-studio"]:
        assert tools_fixtures[slug]["url"] == f"/tools/{slug}"
        assert op.LLM_TOOLS.get(slug, {"default_model": "deepseek-v4-flash"})["default_model"] in {m.id for m in op.CHAT_MODELS}


def test_generate_image_posts_to_openpaths():
    s = Session(Resp({"data": [{"url": "https://x/y.png"}]}))
    assert op.generate_image(op.image_model("flux-schnell"), "a cat", "1024x1024", session=s) == "https://x/y.png"
    url, kw = s.calls[0]
    assert url.endswith("/images/generations") and kw["json"]["aspect_ratio"] == "1:1"
    assert kw["headers"]["Authorization"] == "Bearer k"


def test_video_job_states_and_errors():
    assert op.video_job("j", session=Session(Resp({"status": "completed", "result": {"video_url": "https://v"}}))) == {"status": "completed", "video_url": "https://v"}
    assert op.video_job("j", session=Session(Resp({"status": "queued"})))["status"] == "running"
    with pytest.raises(op.OpenPathsError):
        op.generate_image(op.image_model("flux-schnell"), "x", "1024x1024", session=Session(Resp({"error": {"message": "no"}}, ok=False, status_code=400)))


def test_missing_key_is_503(monkeypatch):
    monkeypatch.delenv("OPENPATHS_API_KEY")
    with pytest.raises(op.OpenPathsError) as e:
        op.chat(op.chat_model("deepseek-v4-flash"), "s", [], 100, session=Session(Resp({})))
    assert e.value.status == 503
