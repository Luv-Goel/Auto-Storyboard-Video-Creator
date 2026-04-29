"""
Unit tests for the transcription module.

Note: These tests mock the faster_whisper model to avoid
loading actual models during testing.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from src.transcription import TranscriptionService
from src.exceptions import TranscriptionError


class TestTranscriptionService:
    """Test cases for TranscriptionService class."""
    
    @pytest.fixture
    def service(self):
        """Create a TranscriptionService instance."""
        with patch('src.transcription.WhisperModel'):
            return TranscriptionService(model_size="base", device="cpu")
    
    def test_init(self):
        """Test initialization."""
        with patch('src.transcription.WhisperModel'):
            service = TranscriptionService(model_size="medium", device="cuda")
            assert service.model_size == "medium"
            assert service.device == "cuda"
            assert service.model is None
    
    def test_load_model(self, service):
        """Test model loading."""
        mock_model = Mock()
        service.model = None
        
        with patch('src.transcription.WhisperModel', return_value=mock_model):
            service.load_model()
        
        assert service.model == mock_model
    
    def test_load_model_already_loaded(self, service):
        """Test that model isn't reloaded if already loaded."""
        mock_model = Mock()
        service.model = mock_model
        
        service.load_model()
        
        # Model should still be the same instance
        assert service.model == mock_model
    
    @patch('os.path.exists', return_value=True)
    def test_transcribe_audio_success(self, mock_exists, service):
        """Test successful audio transcription."""
        # Setup mock model and transcription result
        mock_segment = Mock()
        mock_segment.start = 0.0
        mock_segment.end = 5.0
        mock_segment.text = "Hello world"
        
        mock_info = Mock()
        
        mock_model = Mock()
        mock_model.transcribe.return_value = ([mock_segment], mock_info)
        service.model = mock_model
        
        segments = service.transcribe_audio("test.mp3")
        
        assert len(segments) == 1
        assert segments[0]["start"] == 0.0
        assert segments[0]["end"] == 5.0
        assert segments[0]["text"] == "Hello world"
    
    @patch('os.path.exists', return_value=False)
    def test_transcribe_audio_file_not_found(self, mock_exists, service):
        """Test transcription with non-existent file."""
        with pytest.raises(FileNotFoundError):
            service.transcribe_audio("nonexistent.mp3")
    
    @patch('os.path.exists', return_value=True)
    def test_transcribe_audio_model_not_loaded(self, mock_exists, service):
        """Test that model is loaded automatically."""
        mock_segment = Mock()
        mock_segment.start = 0.0
        mock_segment.end = 5.0
        mock_segment.text = "Hello"
        
        mock_info = Mock()
        mock_model = Mock()
        mock_model.transcribe.return_value = ([mock_segment], mock_info)
        
        with patch('src.transcription.WhisperModel', return_value=mock_model):
            service.model = None
            segments = service.transcribe_audio("test.mp3")
        
        assert len(segments) == 1
    
    @patch('os.path.exists', return_value=True)
    def test_transcribe_audio_segments(self, mock_exists, service):
        """Test transcribe_audio_segments method."""
        # Setup mock segments
        mock_seg1 = Mock()
        mock_seg1.start = 0.0
        mock_seg1.end = 35.0
        mock_seg1.text = "First segment"
        
        mock_seg2 = Mock()
        mock_seg2.start = 35.0
        mock_seg2.end = 65.0
        mock_seg2.text = "Second segment"
        
        mock_info = Mock()
        mock_model = Mock()
        mock_model.transcribe.return_value = ([mock_seg1, mock_seg2], mock_info)
        
        with patch('src.transcription.WhisperModel', return_value=mock_model):
            service.model = None
            segments = service.transcribe_audio_segments("test.mp3", segment_duration=30)
        
        # Should create segments based on duration
        assert len(segments) > 0
        for seg in segments:
            assert "start" in seg
            assert "end" in seg
            assert "text" in seg
