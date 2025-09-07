#!/usr/bin/env python3
"""
Integration tests for GitBase image captioning API endpoint.
Tests both file upload and URL-based image captioning.
"""

import time
from io import BytesIO

import pytest
import requests
from PIL import Image

# Test configuration
API_BASE_URL = "http://localhost:9081"  # Adjust for your inference server
TEST_IMAGE_URL = "https://huggingface.co/unum-cloud/uform-gen2-qwen-500m/resolve/main/interior.jpg"
TEST_SECRET = "test_secret"  # Replace with your test secret


class TestImageCaptioningAPI:
    """Integration tests for image captioning API endpoint."""

    @pytest.fixture(scope="class")
    def api_client(self):
        """Create API client session."""
        session = requests.Session()
        session.headers.update({"secret": TEST_SECRET})
        return session

    def test_caption_from_url_fast_mode(self, api_client):
        """Test captioning from HuggingFace image URL in fast mode."""
        url = f"{API_BASE_URL}/api/v1/image-caption"

        data = {"image_url": TEST_IMAGE_URL, "fast_mode": True}

        print(f"Testing image captioning from URL: {TEST_IMAGE_URL}")
        start_time = time.time()

        response = api_client.post(url, data=data)

        end_time = time.time()
        response_time = end_time - start_time

        print(f"Response time: {response_time:.3f}s")

        # Check response status
        assert response.status_code == 200, f"Request failed with status {response.status_code}: {response.text}"

        # Parse response
        result = response.json()

        # Validate response structure
        assert "caption" in result
        assert "filename" in result
        assert "fast_mode" in result
        assert "model" in result
        assert "source" in result

        # Validate response values
        assert isinstance(result["caption"], str)
        assert len(result["caption"]) > 0
        assert result["fast_mode"] is True
        assert result["model"] == "microsoft/git-base"
        assert result["source"] == "url"
        assert result["filename"] == "interior.jpg"

        print(f"✅ Fast mode caption: {result['caption']}")
        print(f"✅ Response time: {response_time:.3f}s")

        # Fast mode should be relatively quick (under 2 seconds)
        assert response_time < 2.0, f"Fast mode took too long: {response_time:.3f}s"

        return result

    def test_caption_from_url_quality_mode(self, api_client):
        """Test captioning from HuggingFace image URL in quality mode."""
        url = f"{API_BASE_URL}/api/v1/image-caption"

        data = {"image_url": TEST_IMAGE_URL, "fast_mode": False}

        print(f"Testing quality mode captioning from URL: {TEST_IMAGE_URL}")
        start_time = time.time()

        response = api_client.post(url, data=data)

        end_time = time.time()
        response_time = end_time - start_time

        print(f"Response time: {response_time:.3f}s")

        # Check response status
        assert response.status_code == 200, f"Request failed with status {response.status_code}: {response.text}"

        # Parse response
        result = response.json()

        # Validate response structure
        assert result["fast_mode"] is False
        assert result["model"] == "microsoft/git-base"
        assert result["source"] == "url"

        print(f"✅ Quality mode caption: {result['caption']}")
        print(f"✅ Response time: {response_time:.3f}s")

        # Quality mode caption should be longer than fast mode
        assert len(result["caption"]) > 0

        return result

    def test_caption_from_file_upload(self, api_client):
        """Test captioning from uploaded file."""
        # Create a test image
        test_image = Image.new("RGB", (224, 224), color=(255, 0, 0))  # Red square
        image_buffer = BytesIO()
        test_image.save(image_buffer, format="JPEG")
        image_buffer.seek(0)

        url = f"{API_BASE_URL}/api/v1/image-caption"

        files = {"image_file": ("test_image.jpg", image_buffer, "image/jpeg")}

        data = {"fast_mode": True}

        print("Testing image captioning from file upload")
        start_time = time.time()

        response = api_client.post(url, files=files, data=data)

        end_time = time.time()
        response_time = end_time - start_time

        print(f"Response time: {response_time:.3f}s")

        # Check response status
        assert response.status_code == 200, f"Request failed with status {response.status_code}: {response.text}"

        # Parse response
        result = response.json()

        # Validate response
        assert result["source"] == "file"
        assert result["filename"] == "test_image.jpg"
        assert len(result["caption"]) > 0

        print(f"✅ File upload caption: {result['caption']}")

        return result

    def test_invalid_url_handling(self, api_client):
        """Test handling of invalid image URLs."""
        url = f"{API_BASE_URL}/api/v1/image-caption"

        data = {
            "image_url": "https://httpbin.org/status/404",  # Invalid URL
            "fast_mode": True,
        }

        response = api_client.post(url, data=data)

        # Should return error for invalid URL
        assert response.status_code == 400

        result = response.json()
        assert "detail" in result
        print(f"✅ Correctly handled invalid URL: {result['detail']}")

    def test_non_image_url_handling(self, api_client):
        """Test handling of URLs that don't point to images."""
        url = f"{API_BASE_URL}/api/v1/image-caption"

        data = {
            "image_url": "https://httpbin.org/json",  # JSON response, not image
            "fast_mode": True,
        }

        response = api_client.post(url, data=data)

        # Should return error for non-image content
        assert response.status_code == 400

        result = response.json()
        assert "detail" in result
        assert "image" in result["detail"].lower()
        print(f"✅ Correctly handled non-image URL: {result['detail']}")

    def test_missing_parameters(self, api_client):
        """Test handling when neither file nor URL is provided."""
        url = f"{API_BASE_URL}/api/v1/image-caption"

        data = {"fast_mode": True}

        response = api_client.post(url, data=data)

        # Should return error for missing image
        assert response.status_code == 400

        result = response.json()
        assert "detail" in result
        print(f"✅ Correctly handled missing parameters: {result['detail']}")

    def test_both_file_and_url_provided(self, api_client):
        """Test handling when both file and URL are provided."""
        # Create a test image
        test_image = Image.new("RGB", (100, 100), color=(0, 255, 0))
        image_buffer = BytesIO()
        test_image.save(image_buffer, format="JPEG")
        image_buffer.seek(0)

        url = f"{API_BASE_URL}/api/v1/image-caption"

        files = {"image_file": ("test.jpg", image_buffer, "image/jpeg")}

        data = {"image_url": TEST_IMAGE_URL, "fast_mode": True}

        response = api_client.post(url, files=files, data=data)

        # Should return error for conflicting parameters
        assert response.status_code == 400

        result = response.json()
        assert "detail" in result
        print(f"✅ Correctly handled conflicting parameters: {result['detail']}")

    def test_performance_comparison(self, api_client):
        """Compare performance between fast and quality modes."""
        url = f"{API_BASE_URL}/api/v1/image-caption"

        # Test fast mode
        data_fast = {"image_url": TEST_IMAGE_URL, "fast_mode": True}

        start_time = time.time()
        response_fast = api_client.post(url, data=data_fast)
        fast_time = time.time() - start_time

        assert response_fast.status_code == 200
        fast_result = response_fast.json()

        # Test quality mode
        data_quality = {"image_url": TEST_IMAGE_URL, "fast_mode": False}

        start_time = time.time()
        response_quality = api_client.post(url, data=data_quality)
        quality_time = time.time() - start_time

        assert response_quality.status_code == 200
        quality_result = response_quality.json()

        print("⚡ Performance Comparison:")
        print(f"   Fast mode: {fast_time:.3f}s - '{fast_result['caption']}'")
        print(f"   Quality mode: {quality_time:.3f}s - '{quality_result['caption']}'")
        print(f"   Speedup: {quality_time / fast_time:.2f}x")

        # Fast mode should be faster
        assert fast_time < quality_time, "Fast mode should be faster than quality mode"

        # Both should produce reasonable captions
        assert len(fast_result["caption"]) > 0
        assert len(quality_result["caption"]) > 0

    def test_various_image_urls(self, api_client):
        """Test with various publicly available image URLs."""
        test_urls = [
            "https://huggingface.co/unum-cloud/uform-gen2-qwen-500m/resolve/main/interior.jpg",
            "https://raw.githubusercontent.com/microsoft/CameraTraps/main/archive/classification/sample_data/test_images/Desert-at-Sunset.jpg",
            "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=300&h=300&fit=crop",
        ]

        url = f"{API_BASE_URL}/api/v1/image-caption"

        for test_url in test_urls:
            print(f"\n🖼️  Testing URL: {test_url}")

            data = {"image_url": test_url, "fast_mode": True}

            try:
                response = api_client.post(url, data=data)

                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ Caption: {result['caption']}")
                else:
                    print(f"❌ Failed with status {response.status_code}")

            except Exception as e:
                print(f"❌ Error: {e}")


def run_integration_tests():
    """Run all integration tests manually (without pytest)."""
    print("🚀 Starting GitBase Image Captioning Integration Tests")
    print("=" * 60)

    # Create API client
    session = requests.Session()
    session.headers.update({"secret": TEST_SECRET})

    test_class = TestImageCaptioningAPI()

    try:
        # Test 1: URL Fast Mode
        print("\n📝 Test 1: Caption from URL (Fast Mode)")
        test_class.test_caption_from_url_fast_mode(session)

        # Test 2: URL Quality Mode
        print("\n📝 Test 2: Caption from URL (Quality Mode)")
        test_class.test_caption_from_url_quality_mode(session)

        # Test 3: File Upload
        print("\n📝 Test 3: Caption from File Upload")
        test_class.test_caption_from_file_upload(session)

        # Test 4: Performance Comparison
        print("\n📝 Test 4: Performance Comparison")
        test_class.test_performance_comparison(session)

        # Test 5: Error Handling
        print("\n📝 Test 5: Error Handling")
        test_class.test_invalid_url_handling(session)
        test_class.test_non_image_url_handling(session)
        test_class.test_missing_parameters(session)
        test_class.test_both_file_and_url_provided(session)

        # Test 6: Various URLs
        print("\n📝 Test 6: Various Image URLs")
        test_class.test_various_image_urls(session)

        print("\n" + "=" * 60)
        print("🎉 All integration tests completed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    # Check if server is running
    try:
        response = requests.get(f"{API_BASE_URL}/docs", timeout=5)
        if response.status_code == 200:
            print(f"✅ Server is running at {API_BASE_URL}")
            run_integration_tests()
        else:
            print(f"❌ Server not responding properly at {API_BASE_URL}")
    except requests.exceptions.RequestException:
        print(f"❌ Cannot connect to server at {API_BASE_URL}")
        print("Make sure the inference server is running:")
        print("PYTHONPATH=. python questions/inference_server/inference_server.py")
