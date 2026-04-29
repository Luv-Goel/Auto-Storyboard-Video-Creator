"""
Pytest configuration and shared fixtures for Video Creator tests.
"""

import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.keyword_extraction import KeywordExtractor
from src.transcription import TranscriptionService
from src.api_client import PexelsClient
from src.exceptions import VideoCreatorError


@pytest.fixture
def keyword_extractor() -> KeywordExtractor:
    """Fixture for KeywordExtractor instance."""
    return KeywordExtractor()


@pytest.fixture
def sample_text() -> str:
    """Fixture for sample text for testing."""
    return "The quick brown fox jumps over the lazy dog in the beautiful garden near the river."


@pytest.fixture
def sample_segments() -> list:
    """Fixture for sample transcription segments."""
    return [
        {"start": 0.0, "end": 5.0, "text": "Hello world this is a test"},
        {"start": 5.0, "end": 10.0, "text": "This is another segment with mountains and rivers"},
        {"start": 10.0, "end": 15.0, "text": ""},  # Empty segment
    ]


@pytest.fixture
def mock_pexels_response_image() -> dict:
    """Mock Pexels API response for image search."""
    return {
        "photos": [
            {
                "id": 12345,
                "src": {
                    "original": "https://images.pexels.com/photos/12345/photo.jpg"
                }
            }
        ]
    }


@pytest.fixture
def mock_pexels_response_video() -> dict:
    """Mock Pexels API response for video search."""
    return {
        "videos": [
            {
                "id": 67890,
                "video_files": [
                    {"link": "https://example.com/video.mp4", "height": 1080},
                    {"link": "https://example.com/video_low.mp4", "height": 720}
                ]
            }
        ]
    }
