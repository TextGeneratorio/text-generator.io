"""
Comprehensive unit tests for GitBase image captioning module.
Tests functionality, performance optimizations, and compatibility.
"""

import pytest
import torch
import time
import os
from PIL import Image
from io import BytesIO
import logging
from unittest.mock import Mock, patch, MagicMock

from questions.image_captioning.gitbase_captioner import (
    GitBaseCaptioner,
    get_gitbase_captioner,
    caption_image_bytes
)
from questions.logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

class TestGitBaseCaptioner:
    """Test cases for GitBaseCaptioner class."""
    
    @pytest.fixture
    def sample_image(self):
        """Create a sample RGB image for testing."""
        return Image.new('RGB', (224, 224), color=(255, 0, 0))  # Red image
    
    @pytest.fixture
    def sample_image_bytes(self, sample_image):
        """Create sample image bytes for testing."""
        buffer = BytesIO()
        sample_image.save(buffer, format='JPEG')
        return buffer.getvalue()
    
    @pytest.fixture
    def captioner(self):
        """Create a GitBaseCaptioner instance for testing."""
        return GitBaseCaptioner(
            dtype=torch.float32,  # Use float32 for CPU testing
            device="cpu",  # Use CPU for CI compatibility
            use_compile=False,  # Disable compile for compatibility
            use_channels_last=False  # Disable for CPU
        )
    
    def test_initialization(self):
        """Test GitBaseCaptioner initialization with different parameters."""
        # Test default initialization
        captioner = GitBaseCaptioner()
        assert captioner.model_name == "microsoft/git-base"
        assert captioner.dtype == torch.float16
        assert captioner.device == "cuda"
        assert captioner.use_compile is True
        assert captioner.use_channels_last is True
        assert not captioner._is_loaded
        assert not captioner._warmup_done
        
        # Test custom initialization
        captioner = GitBaseCaptioner(
            model_name="custom/model",
            dtype=torch.float32,
            device="cpu",
            use_compile=False,
            use_channels_last=False
        )
        assert captioner.model_name == "custom/model"
        assert captioner.dtype == torch.float32
        assert captioner.device == "cpu"
        assert captioner.use_compile is False
        assert captioner.use_channels_last is False
    
    @patch('questions.image_captioning.gitbase_captioner.AutoProcessor.from_pretrained')
    @patch('questions.image_captioning.gitbase_captioner.AutoModelForVision2Seq.from_pretrained')
    def test_load_model(self, mock_model, mock_processor, captioner):
        """Test model loading functionality."""
        # Setup mocks
        mock_processor_instance = Mock()
        mock_model_instance = Mock()
        mock_model_instance.to.return_value = mock_model_instance
        
        mock_processor.return_value = mock_processor_instance
        mock_model.return_value = mock_model_instance
        
        # Test model loading
        captioner.load()
        
        # Verify calls
        mock_processor.assert_called_once_with("microsoft/git-base")
        mock_model.assert_called_once_with(
            "microsoft/git-base",
            torch_dtype=torch.float32
        )
        mock_model_instance.to.assert_called_with("cpu")
        
        assert captioner._is_loaded is True
        assert captioner.processor == mock_processor_instance
        assert captioner.model == mock_model_instance
    
    @patch('questions.image_captioning.gitbase_captioner.AutoProcessor.from_pretrained')
    @patch('questions.image_captioning.gitbase_captioner.AutoModelForVision2Seq.from_pretrained')
    def test_warmup(self, mock_model, mock_processor, captioner):
        """Test model warmup functionality."""
        # Setup mocks
        mock_processor_instance = Mock()
        mock_model_instance = Mock()
        mock_model_instance.to.return_value = mock_model_instance
        mock_model_instance.generate.return_value = torch.tensor([[1, 2, 3]])
        
        mock_processor.return_value = mock_processor_instance
        mock_model.return_value = mock_model_instance
        
        # Setup processor mock to return expected format
        mock_inputs = {'pixel_values': torch.randn(1, 3, 224, 224)}
        mock_processor_instance.return_value = mock_inputs
        
        # Test warmup
        captioner.load()
        captioner._warmup()
        
        # Verify warmup was called
        assert captioner._warmup_done is True
        mock_model_instance.generate.assert_called()
    
    @patch('questions.image_captioning.gitbase_captioner.AutoProcessor.from_pretrained')
    @patch('questions.image_captioning.gitbase_captioner.AutoModelForVision2Seq.from_pretrained')
    def test_caption_image(self, mock_model, mock_processor, captioner, sample_image):
        """Test image captioning functionality."""
        # Setup mocks
        mock_processor_instance = Mock()
        mock_model_instance = Mock()
        mock_model_instance.to.return_value = mock_model_instance
        mock_model_instance.generate.return_value = torch.tensor([[101, 102, 103]])
        
        mock_processor.return_value = mock_processor_instance
        mock_model.return_value = mock_model_instance
        
        # Setup processor mocks
        mock_inputs = {'pixel_values': torch.randn(1, 3, 224, 224)}
        mock_processor_instance.return_value = mock_inputs
        mock_processor_instance.batch_decode.return_value = ["a red image"]
        
        # Test captioning
        caption = captioner.caption_image(sample_image)
        
        # Verify result
        assert caption == "a red image"
        mock_processor_instance.assert_called_with(images=sample_image, return_tensors="pt")
        mock_model_instance.generate.assert_called()
        mock_processor_instance.batch_decode.assert_called_with(
            torch.tensor([[101, 102, 103]]), 
            skip_special_tokens=True
        )
    
    @patch('questions.image_captioning.gitbase_captioner.AutoProcessor.from_pretrained')
    @patch('questions.image_captioning.gitbase_captioner.AutoModelForVision2Seq.from_pretrained')
    def test_caption_image_fast(self, mock_model, mock_processor, captioner, sample_image):
        """Test fast captioning mode."""
        # Setup mocks
        mock_processor_instance = Mock()
        mock_model_instance = Mock()
        mock_model_instance.to.return_value = mock_model_instance
        mock_model_instance.generate.return_value = torch.tensor([[101, 102]])
        
        mock_processor.return_value = mock_processor_instance
        mock_model.return_value = mock_model_instance
        
        # Setup processor mocks
        mock_inputs = {'pixel_values': torch.randn(1, 3, 224, 224)}
        mock_processor_instance.return_value = mock_inputs
        mock_processor_instance.batch_decode.return_value = ["red"]
        
        # Test fast captioning
        caption = captioner.caption_image_fast(sample_image)
        
        # Verify result and parameters
        assert caption == "red"
        
        # Check that generate was called with fast parameters
        call_args = mock_model_instance.generate.call_args
        assert call_args[1]['max_length'] == 10
        assert call_args[1]['num_beams'] == 1
        assert call_args[1]['do_sample'] is False
    
    @patch('questions.image_captioning.gitbase_captioner.AutoProcessor.from_pretrained')
    @patch('questions.image_captioning.gitbase_captioner.AutoModelForVision2Seq.from_pretrained')
    def test_caption_image_quality(self, mock_model, mock_processor, captioner, sample_image):
        """Test quality captioning mode."""
        # Setup mocks
        mock_processor_instance = Mock()
        mock_model_instance = Mock()
        mock_model_instance.to.return_value = mock_model_instance
        mock_model_instance.generate.return_value = torch.tensor([[101, 102, 103, 104]])
        
        mock_processor.return_value = mock_processor_instance
        mock_model.return_value = mock_model_instance
        
        # Setup processor mocks
        mock_inputs = {'pixel_values': torch.randn(1, 3, 224, 224)}
        mock_processor_instance.return_value = mock_inputs
        mock_processor_instance.batch_decode.return_value = ["a detailed red image"]
        
        # Test quality captioning
        caption = captioner.caption_image_quality(sample_image)
        
        # Verify result and parameters
        assert caption == "a detailed red image"
        
        # Check that generate was called with quality parameters
        call_args = mock_model_instance.generate.call_args
        assert call_args[1]['max_length'] == 30
        assert call_args[1]['num_beams'] == 3
        assert call_args[1]['do_sample'] is False
    
    @patch('questions.image_captioning.gitbase_captioner.AutoProcessor.from_pretrained')
    @patch('questions.image_captioning.gitbase_captioner.AutoModelForVision2Seq.from_pretrained')
    def test_benchmark(self, mock_model, mock_processor, captioner, sample_image):
        """Test benchmarking functionality."""
        # Setup mocks
        mock_processor_instance = Mock()
        mock_model_instance = Mock()
        mock_model_instance.to.return_value = mock_model_instance
        mock_model_instance.generate.return_value = torch.tensor([[101, 102]])
        
        mock_processor.return_value = mock_processor_instance
        mock_model.return_value = mock_model_instance
        
        # Setup processor mocks
        mock_inputs = {'pixel_values': torch.randn(1, 3, 224, 224)}
        mock_processor_instance.return_value = mock_inputs
        mock_processor_instance.batch_decode.return_value = ["test"]
        
        # Test benchmarking
        results = captioner.benchmark(sample_image, num_runs=2)
        
        # Verify results structure
        assert 'fast_mode' in results
        assert 'quality_mode' in results
        assert isinstance(results['fast_mode'], float)
        assert isinstance(results['quality_mode'], float)
        assert results['fast_mode'] > 0
        assert results['quality_mode'] > 0


class TestModuleFunctions:
    """Test module-level functions."""
    
    @patch('questions.image_captioning.gitbase_captioner._GITBASE_CACHE')
    def test_get_gitbase_captioner(self, mock_cache):
        """Test cached captioner retrieval."""
        mock_captioner = Mock()
        mock_cache.add_or_get.return_value = mock_captioner
        
        # Test function call
        result = get_gitbase_captioner(
            dtype=torch.float16,
            use_compile=True,
            use_channels_last=False
        )
        
        # Verify cache was called correctly
        assert result == mock_captioner
        mock_cache.add_or_get.assert_called_once()
        cache_key = mock_cache.add_or_get.call_args[0][0]
        assert "gitbase_" in cache_key
        assert "torch.float16" in cache_key
        assert "True" in cache_key
        assert "False" in cache_key
    
    def test_caption_image_bytes(self, sample_image):
        """Test caption_image_bytes function."""
        # Convert sample image to bytes
        buffer = BytesIO()
        sample_image.save(buffer, format='JPEG')
        image_bytes = buffer.getvalue()
        
        with patch('questions.image_captioning.gitbase_captioner.get_gitbase_captioner') as mock_get_captioner:
            mock_captioner = Mock()
            mock_captioner.caption_image_fast.return_value = "fast caption"
            mock_captioner.caption_image_quality.return_value = "quality caption"
            mock_get_captioner.return_value = mock_captioner
            
            # Test fast mode
            result_fast = caption_image_bytes(image_bytes, fast_mode=True)
            assert result_fast == "fast caption"
            mock_captioner.caption_image_fast.assert_called_once()
            
            # Test quality mode
            result_quality = caption_image_bytes(image_bytes, fast_mode=False)
            assert result_quality == "quality caption"
            mock_captioner.caption_image_quality.assert_called_once()


class TestPerformanceOptimizations:
    """Test performance optimization features."""
    
    def test_dtype_configurations(self):
        """Test different dtype configurations."""
        # Test float16
        captioner_fp16 = GitBaseCaptioner(dtype=torch.float16, device="cpu")
        assert captioner_fp16.dtype == torch.float16
        
        # Test bfloat16
        captioner_bf16 = GitBaseCaptioner(dtype=torch.bfloat16, device="cpu")
        assert captioner_bf16.dtype == torch.bfloat16
        
        # Test float32
        captioner_fp32 = GitBaseCaptioner(dtype=torch.float32, device="cpu")
        assert captioner_fp32.dtype == torch.float32
    
    def test_optimization_flags(self):
        """Test optimization flags are properly set."""
        # Test with all optimizations enabled
        captioner_optimized = GitBaseCaptioner(
            use_compile=True,
            use_channels_last=True
        )
        assert captioner_optimized.use_compile is True
        assert captioner_optimized.use_channels_last is True
        
        # Test with optimizations disabled
        captioner_basic = GitBaseCaptioner(
            use_compile=False,
            use_channels_last=False
        )
        assert captioner_basic.use_compile is False
        assert captioner_basic.use_channels_last is False
    
    @patch('torch.compile')
    @patch('questions.image_captioning.gitbase_captioner.AutoProcessor.from_pretrained')
    @patch('questions.image_captioning.gitbase_captioner.AutoModelForVision2Seq.from_pretrained')
    def test_torch_compile_integration(self, mock_model, mock_processor, mock_compile):
        """Test torch.compile integration."""
        # Setup mocks
        mock_processor_instance = Mock()
        mock_model_instance = Mock()
        mock_compiled_model = Mock()
        
        mock_processor.return_value = mock_processor_instance
        mock_model.return_value = mock_model_instance
        mock_model_instance.to.return_value = mock_model_instance
        mock_compile.return_value = mock_compiled_model
        
        # Test with compile enabled
        captioner = GitBaseCaptioner(use_compile=True, device="cpu")
        
        with patch('torch.__version__', "2.0.0"):
            captioner.load()
        
        # Verify torch.compile was called
        mock_compile.assert_called_once_with(mock_model_instance)


class TestIntegrationWithExistingCode:
    """Test integration with existing codebase patterns."""
    
    def test_model_cache_integration(self):
        """Test integration with existing model cache system."""
        from questions.inference_server.model_cache import ModelCache
        
        # Test that we can create multiple captioners
        captioner1 = get_gitbase_captioner(dtype=torch.float16)
        captioner2 = get_gitbase_captioner(dtype=torch.float16)
        
        # They should be the same instance due to caching
        assert captioner1 is captioner2
    
    def test_logging_integration(self):
        """Test logging integration."""
        with patch('questions.image_captioning.gitbase_captioner.logger') as mock_logger:
            captioner = GitBaseCaptioner(device="cpu")
            
            # This should trigger logging during model loading
            with patch('questions.image_captioning.gitbase_captioner.AutoProcessor.from_pretrained'):
                with patch('questions.image_captioning.gitbase_captioner.AutoModelForVision2Seq.from_pretrained') as mock_model:
                    mock_model_instance = Mock()
                    mock_model_instance.to.return_value = mock_model_instance
                    mock_model.return_value = mock_model_instance
                    
                    captioner.load()
                    
                    # Verify logging was called
                    mock_logger.info.assert_called()


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    def test_invalid_image_handling(self):
        """Test handling of invalid images."""
        captioner = GitBaseCaptioner(device="cpu")
        
        # Test with None image
        with pytest.raises(AttributeError):
            captioner.caption_image(None)
    
    def test_model_loading_failure(self):
        """Test handling of model loading failures."""
        with patch('questions.image_captioning.gitbase_captioner.AutoModelForVision2Seq.from_pretrained') as mock_model:
            mock_model.side_effect = Exception("Model loading failed")
            
            captioner = GitBaseCaptioner(device="cpu")
            
            with pytest.raises(Exception, match="Model loading failed"):
                captioner.load()
    
    def test_invalid_bytes_input(self):
        """Test handling of invalid byte input."""
        with pytest.raises(Exception):
            caption_image_bytes(b"invalid image data")


@pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA not available")
class TestCUDAOptimizations:
    """Test CUDA-specific optimizations (only run if CUDA is available)."""
    
    def test_cuda_device_usage(self):
        """Test CUDA device usage."""
        captioner = GitBaseCaptioner(device="cuda")
        assert captioner.device == "cuda"
    
    def test_channels_last_with_cuda(self):
        """Test channels_last memory format with CUDA."""
        captioner = GitBaseCaptioner(
            device="cuda",
            use_channels_last=True
        )
        assert captioner.use_channels_last is True


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])