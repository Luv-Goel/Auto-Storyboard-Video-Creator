"""
Unit tests for the video generator module.

Note: These tests use extensive mocking to avoid actual video processing.
"""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock, call
from pathlib import Path

from src.video_generator import VideoGenerator
from src.exceptions import InvalidAudioFileError, VideoRenderError


class TestVideoGenerator:
    """Test cases for VideoGenerator class."""
    
    @pytest.fixture
    def mock_dependencies(self):
        """Mock all external dependencies."""
        with patch('src.video_generator.TranscriptionService') as mock_trans, \
             patch('src.video_generator.KeywordExtractor') as mock_keyword, \
             patch('src.video_generator.PexelsClient') as mock_pexels, \
             patch('src.video_generator.VIDEO_RESOLUTION', (1920, 1080)), \
             patch('os.makedirs'):
            yield {
                'transcriber': mock_trans.return_value,
                'keyword_extractor': mock_keyword.return_value,
                'pexels_client': mock_pexels.return_value
            }
    
    @pytest.fixture
    def generator(self, mock_dependencies):
        """Create a VideoGenerator with mocked dependencies."""
        with patch('src.video_generator.PEXELS_API_KEYS', ['test_key']):
            gen = VideoGenerator(
                pexels_api_keys=['test_key'],
                aspect_ratio="16:9",
                progress_callback=None
            )
            return gen
    
    def test_init_with_keys(self):
        """Test initialization with API keys."""
        with patch('src.video_generator.PexelsClient'), \
             patch('os.makedirs'):
            gen = VideoGenerator(
                pexels_api_keys=['key1', 'key2'],
                aspect_ratio="16:9"
            )
            assert len(gen.api_keys) == 2
            assert gen.aspect_ratio == "16:9"
    
    def test_init_no_keys(self):
        """Test initialization without API keys."""
        with patch('src.video_generator.PEXELS_API_KEYS', []), \
             patch('src.video_generator.PexelsClient'), \
             patch('os.makedirs'):
            gen = VideoGenerator(pexels_api_keys=[])
            assert gen.api_keys == []
            assert gen.pexels_client is None
    
    def test_init_aspect_ratio(self):
        """Test aspect ratio handling."""
        with patch('src.video_generator.PexelsClient'), \
             patch('src.video_generator.ASPECT_RATIOS', {"16:9": (1920, 1080)}), \
             patch('os.makedirs'):
            gen = VideoGenerator(aspect_ratio="16:9")
            assert gen.resolution == (1920, 1080)
    
    def test_log_progress(self, generator):
        """Test progress logging."""
        mock_callback = Mock()
        generator.progress_callback = mock_callback
        
        generator._log_progress("Test message", 50)
        
        mock_callback.assert_called_once_with("Test message", 50)
    
    def test_prepare_segment_data(self, generator):
        """Test segment data preparation."""
        generator.keyword_extractor.get_search_query.return_value = "mountain river"
        generator.keyword_extractor.extract_keywords.return_value = ["mountain", "river"]
        
        segments = [
            {"start": 0.0, "end": 10.0, "text": "Mountains and rivers are beautiful"},
            {"start": 10.0, "end": 20.0, "text": ""},  # Empty text
        ]
        
        with patch('random.choice', return_value="nature"):
            segment_data = generator._prepare_segment_data(segments)
        
        assert len(segment_data) == 2
        assert segment_data[0]["keywords"] == ["mountain", "river"]
        assert segment_data[1]["query"] == "nature"  # Fallback
    
    @patch('os.path.exists', return_value=False)
    def test_generate_video_file_not_found(self, mock_exists, generator):
        """Test video generation with non-existent file."""
        with pytest.raises(InvalidAudioFileError):
            generator.generate_video("nonexistent.mp3")
    
    @patch('os.path.exists', return_value=True)
    def test_generate_video_pipeline(self, mock_exists, generator):
        """Test full video generation pipeline."""
        # Setup mocks
        generator.transcriber.transcribe_audio_segments.return_value = [
            {"start": 0.0, "end": 10.0, "text": "Test segment"}
        ]
        generator.keyword_extractor.get_search_query.return_value = "test"
        generator.keyword_extractor.extract_keywords.return_value = ["test"]
        generator.pexels_client.search_images.return_value = []
        generator.pexels_client.search_videos.return_value = []
        
        with patch.object(generator, '_build_video_pass', return_value="output.mp4"), \
             patch.object(generator, '_create_color_placeholder', return_value="placeholder.jpg"):
            result = generator.generate_video("test.mp3")
        
        assert result == "output.mp4"
        generator.transcriber.transcribe_audio_segments.assert_called_once()
    
    def test_create_color_placeholder(self, generator):
        """Test placeholder image creation."""
        with patch('PIL.Image.new') as mock_img, \
             patch('PIL.ImageDraw.Draw'), \
             patch('os.path.join', return_value="test.jpg"):
            mock_img.return_value.save = Mock()
            result = generator._create_color_placeholder(0)
            assert result == "test.jpg"
    
    def test_resize_and_crop_clip(self, generator):
        """Test clip resizing and cropping."""
        mock_clip = Mock()
        mock_clip.size = (1280, 720)
        mock_clip.resized.return_value = mock_clip
        mock_clip.cropped.return_value = mock_clip
        
        result = generator._resize_and_crop_clip(mock_clip)
        
        mock_clip.resized.assert_called_once()
        mock_clip.cropped.assert_called_once()
    
    def test_find_audio_file_exists(self, generator):
        """Test finding existing audio file."""
        generator.current_audio_path = "test.mp3"
        with patch('os.path.exists', return_value=True):
            result = generator._find_audio_file()
            assert result == "test.mp3"
    
    def test_find_audio_file_not_found(self, generator):
        """Test when audio file doesn't exist."""
        generator.current_audio_path = "nonexistent.mp3"
        with patch('os.path.exists', return_value=False):
            result = generator._find_audio_file()
            assert result is None
