import pytest

pytestmark = [pytest.mark.integration, pytest.mark.inference]

@pytest.mark.skipif(True, reason="Summarization tests require inference dependencies")
def test_extractive_summary():
    """Test extractive summary functionality (skipped by default)"""
    pass
