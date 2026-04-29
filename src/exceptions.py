"""
Custom exceptions for the Video Creator application.

This module defines all custom exceptions used throughout the application
for better error handling and debugging.
"""


class VideoCreatorError(Exception):
    """Base exception for all Video Creator errors."""
    pass


class ConfigurationError(VideoCreatorError):
    """Raised when there is a configuration issue."""
    pass


class APIError(VideoCreatorError):
    """Raised when an external API request fails."""
    
    def __init__(self, message: str, status_code: int = None, response: str = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class TranscriptionError(VideoCreatorError):
    """Raised when audio transcription fails."""
    pass


class KeywordExtractionError(VideoCreatorError):
    """Raised when keyword extraction fails."""
    pass


class MediaFetchError(VideoCreatorError):
    """Raised when fetching media from external sources fails."""
    pass


class VideoRenderError(VideoCreatorError):
    """Raised when video rendering fails."""
    pass


class InvalidAudioFileError(VideoCreatorError):
    """Raised when the audio file is invalid or cannot be processed."""
    pass


class RateLimitError(VideoCreatorError):
    """Raised when an API rate limit is exceeded."""
    pass


class MediaNotFoundError(VideoCreatorError):
    """Raised when requested media cannot be found."""
    pass


class JobError(VideoCreatorError):
    """Raised when there is an issue with job processing."""
    pass
