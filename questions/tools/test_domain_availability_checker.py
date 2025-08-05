import aiohttp
import pytest
import asyncio
from domain_availability_checker import check_domain_availability, check_domain_availability_async

def test_synthai_co_availability():
    result = check_domain_availability("synthaiasdf.co")
    assert result == "Available", "synthaiasdf.co should be available"

def test_soundforgeai_availability():
    result = check_domain_availability("soundforge.ai")
    assert result == "Available", "soundforge.ai should be available"

def test_google_com_availability():
    result = check_domain_availability("google.com")
    assert result == "Taken", "google.com should be taken"

@pytest.mark.asyncio
async def test_check_domain_availability_async():
    async with aiohttp.ClientSession() as session:
        result = await check_domain_availability_async("synthaiasdf.co", session)
        assert result == "Available", "synthaiasdf.co should be available"

        result = await check_domain_availability_async("google.com", session)
        assert result == "Taken", "google.com should be taken"

# You can add more test cases here as needed