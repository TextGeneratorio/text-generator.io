import pytest
from domain_availability_checker import check_domain_availability

def test_synthai_co_availability():
    result = check_domain_availability("synthaiasdf.co")
    assert result == "Available", "synthaiasdf.co should be available"

def test_google_com_availability():
    result = check_domain_availability("google.com")
    assert result == "Taken", "google.com should be taken"

# You can add more test cases here as needed