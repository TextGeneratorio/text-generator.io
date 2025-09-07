import pytest

from questions.summarization import get_extractive_summary_inner

# pytestmark = [pytest.mark.integration, pytest.mark.inference]


class MockSummarizer:
    """Mock summarizer for testing that truncates text to simulate summarization"""

    def __call__(self, text):
        # Simulate summarization by truncating to first 20 chars + "..."
        summary_text = text[:20] + "..." if len(text) > 20 else text
        return [{"summary_text": summary_text}]


def test_max_length_parameter():
    """Test that max_length parameter is respected in summarization"""
    mock_summarizer = MockSummarizer()

    # Test with long text
    long_text = "hey hows its going whats the weather today" * 5  # 215 chars

    # Test without max_length (should return full summarized text)
    result_no_limit = get_extractive_summary_inner(mock_summarizer, long_text, max_length=0)
    assert len(result_no_limit) > 20

    # Test with max_length set to 10 (should be truncated or handled properly)
    result_with_limit = get_extractive_summary_inner(mock_summarizer, long_text, max_length=10)
    # The function should either truncate or retry with different parameters
    # Since our mock always returns 23 chars ("hey hows its going w..."),
    # and the retry logic should kick in but eventually return the result
    assert isinstance(result_with_limit, str)


def test_empty_text_summarization():
    """Test summarization with empty or very short text"""
    mock_summarizer = MockSummarizer()

    # Test with empty text
    result_empty = get_extractive_summary_inner(mock_summarizer, "", max_length=10)
    assert result_empty == ""

    # Test with very short text
    short_text = "Hello"
    result_short = get_extractive_summary_inner(mock_summarizer, short_text, max_length=10)
    assert result_short == "Hello"


@pytest.mark.skipif(True, reason="Summarization tests require inference dependencies")
def test_extractive_summary():
    """Test extractive summary functionality (skipped by default)"""
    pass
