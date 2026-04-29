"""
Unit tests for the exceptions module.
"""

import pytest

from src.exceptions import (
    VideoCreatorError,
    ConfigurationError,
    APIError,
    TranscriptionError,
    KeywordExtractionError,
    MediaFetchError,
    VideoRenderError,
    InvalidAudioFileError,
    RateLimitError,
    MediaNotFoundError,
    JobError
)


class TestExceptions:
    """Test cases for custom exceptions."""
    
    def test_base_exception(self):
        """Test that VideoCreatorError is the base exception."""
        exc = VideoCreatorError("test")
        assert str(exc) == "test"
        assert isinstance(exc, Exception)
    
    def test_configuration_error(self):
        """Test ConfigurationError."""
        exc = ConfigurationError("config error")
        assert str(exc) == "config error"
        assert isinstance(exc, VideoCreatorError)
    
    def test_api_error_basic(self):
        """Test APIError with basic message."""
        exc = APIError("api error")
        assert str(exc) == "api error"
        assert exc.status_code is None
        assert exc.response is None
        assert isinstance(exc, VideoCreatorError)
    
    def test_api_error_with_status(self):
        """Test APIError with status code."""
        exc = APIError("api error", status_code=404, response="Not found")
        assert exc.status_code == 404
        assert exc.response == "Not found"
    
    def test_transcription_error(self):
        """Test TranscriptionError."""
        exc = TranscriptionError("transcription failed")
        assert isinstance(exc, VideoCreatorError)
    
    def test_keyword_extraction_error(self):
        """Test KeywordExtractionError."""
        exc = KeywordExtractionError("extraction failed")
        assert isinstance(exc, VideoCreatorError)
    
    def test_media_fetch_error(self):
        """Test MediaFetchError."""
        exc = MediaFetchError("fetch failed")
        assert isinstance(exc, VideoCreatorError)
    
    def test_video_render_error(self):
        """Test VideoRenderError."""
        exc = VideoRenderError("render failed")
        assert isinstance(exc, VideoCreatorError)
    
    def test_invalid_audio_file_error(self):
        """Test InvalidAudioFileError."""
        exc = InvalidAudioFileError("invalid file")
        assert isinstance(exc, VideoCreatorError)
    
    def test_rate_limit_error(self):
        """Test RateLimitError."""
        exc = RateLimitError("rate limited")
        assert isinstance(exc, VideoCreatorError)
    
    def test_media_not_found_error(self):
        """Test MediaNotFoundError."""
        exc = MediaNotFoundError("not found")
        assert isinstance(exc, VideoCreatorError)
    
    def test_job_error(self):
        """Test JobError."""
        exc = JobError("job failed")
        assert isinstance(exc, VideoCreatorError)
    
    def test_exception_hierarchy(self):
        """Test that all exceptions inherit from VideoCreatorError."""
        exceptions = [
            ConfigurationError("test"),
            APIError("test"),
            TranscriptionError("test"),
            KeywordExtractionError("test"),
            MediaFetchError("test"),
            VideoRenderError("test"),
            InvalidAudioFileError("test"),
            RateLimitError("test"),
            MediaNotFoundError("test"),
            JobError("test")
        ]
        
        for exc in exceptions:
            assert isinstance(exc, VideoCreatorError)
