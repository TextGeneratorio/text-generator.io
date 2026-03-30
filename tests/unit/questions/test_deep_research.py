from questions.deep_research import (
    ResearchSource,
    extract_json_object,
    normalize_search_result_url,
    run_deep_research,
    select_image_urls,
)


def test_extract_json_object_handles_fenced_payload():
    payload = """```json
    {"title":"Demo","search_queries":["alpha","beta"]}
    ```"""
    result = extract_json_object(payload)
    assert result["title"] == "Demo"
    assert result["search_queries"] == ["alpha", "beta"]


def test_normalize_search_result_url_unwraps_duckduckgo_redirect():
    raw = "https://duckduckgo.com/l/?uddg=https%3A%2F%2Fexample.com%2Freport"
    assert normalize_search_result_url(raw) == "https://example.com/report"


def test_select_image_urls_prefers_recommended_indices():
    sources = [
        ResearchSource(
            title="One",
            url="https://example.com/1",
            domain="example.com",
            query="demo",
            snippet="a" * 200,
            image_url="https://img.example.com/1.jpg",
        ),
        ResearchSource(
            title="Two",
            url="https://example.com/2",
            domain="example.com",
            query="demo",
            snippet="b" * 200,
            image_url="https://img.example.com/2.jpg",
        ),
    ]
    images = select_image_urls(sources, {"recommended_images": [2]})
    assert images[0] == "https://img.example.com/2.jpg"
    assert "https://img.example.com/1.jpg" in images


def test_run_deep_research_assembles_final_payload(monkeypatch):
    messages = [{"role": "user", "content": "Research OCR APIs"}]
    sources = [
        ResearchSource(
            title="OCR One",
            url="https://example.com/ocr-one",
            domain="example.com",
            query="ocr apis",
            snippet="OCR One is fast and cheap.",
            image_url="https://img.example.com/ocr-one.jpg",
        ),
        ResearchSource(
            title="OCR Two",
            url="https://example.com/ocr-two",
            domain="example.com",
            query="ocr apis",
            snippet="OCR Two focuses on enterprise security.",
        ),
    ]

    monkeypatch.setattr(
        "questions.deep_research.build_plan",
        lambda incoming: {
            "title": "OCR API Research",
            "user_question": incoming[-1]["content"],
            "search_queries": ["ocr apis"],
            "angle": "Compare pricing and speed",
            "must_cover": ["pricing", "latency"],
            "answer_format": "brief",
        },
    )
    monkeypatch.setattr("questions.deep_research.collect_sources", lambda plan, max_sources: sources)
    monkeypatch.setattr(
        "questions.deep_research.distill_sources",
        lambda plan, collected: {
            "overview": "Two solid OCR vendors surfaced.",
            "recommended_images": [1],
        },
    )
    monkeypatch.setattr(
        "questions.deep_research.build_report",
        lambda plan, analysis, collected: "# OCR API Research\n\n- OCR One is cheaper.\n- OCR Two is more security-focused.",
    )

    result = run_deep_research(messages, max_sources=4)

    assert result["title"] == "OCR API Research"
    assert result["question"] == "Research OCR APIs"
    assert len(result["sources"]) == 2
    assert result["images"] == ["https://img.example.com/ocr-one.jpg"]
    assert result["report_markdown"].startswith("# OCR API Research")
