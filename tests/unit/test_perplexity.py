import pytest

pytestmark = [pytest.mark.integration, pytest.mark.inference]

@pytest.mark.skipif(True, reason="Perplexity tests require inference dependencies")
def test_perplexity_basic():
    """Test perplexity functionality (skipped by default)"""
    pass
