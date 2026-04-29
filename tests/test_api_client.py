"""
Unit tests for the Pexels API client module.

Note: These tests use mocking to avoid actual API calls.
"""

import pytest
import requests
from unittest.mock import Mock, patch, MagicMock

from src.api_client import PexelsClient
from src.exceptions import MediaFetchError


class TestPexelsClient:
    """Test cases for PexelsClient class."""
    
    @pytest.fixture
    def client(self):
        """Create a PexelsClient with test API key."""
        return PexelsClient(api_keys=["test_key_12345"])
    
    def test_init_with_keys(self):
        """Test initialization with API keys."""
        client = PexelsClient(api_keys=["key1", "key2"])
        assert len(client.api_keys) == 2
        assert client.api_key == "key1"
        assert client.current_key_index == 0
    
    def test_init_no_keys(self):
        """Test initialization with no keys raises ValueError."""
        with pytest.raises(ValueError):
            PexelsClient(api_keys=[])
    
    def test_rotate_key(self, client):
        """Test API key rotation."""
        client.api_keys = ["key1", "key2", "key3"]
        original_key = client.api_key
        
        client._rotate_key()
        
        assert client.current_key_index == 1
        assert client.api_key == "key2"
        assert client.request_count == 0
    
    def test_rotate_key_wraps(self, client):
        """Test that key rotation wraps around."""
        client.api_keys = ["key1", "key2"]
        client.current_key_index = 1
        client.api_key = "key2"
        
        client._rotate_key()
        
        assert client.current_key_index == 0
        assert client.api_key == "key1"
    
    @patch('src.api_client.requests.Session')
    def test_search_images_success(self, mock_session, client):
        """Test successful image search."""
        # Setup mock response
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "photos": [
                {"id": 1, "src": {"original": "http://example.com/img.jpg"}}
            ]
        }
        mock_session.return_value.get.return_value = mock_resp
        
        client.session = mock_session.return_value
        
        results = client.search_images("nature")
        
        assert len(results) == 1
        assert results[0]["id"] == 1
    
    @patch('src.api_client.requests.Session')
    def test_search_images_rate_limit(self, mock_session, client):
        """Test handling of rate limit (429)."""
        # Setup mock to return 429 then success
        mock_resp_429 = Mock()
        mock_resp_429.status_code = 429
        
        mock_resp_ok = Mock()
        mock_resp_ok.status_code = 200
        mock_resp_ok.json.return_value = {"photos": []}
        
        client.session = mock_session.return_value
        client.api_keys = ["key1", "key2"]  # Need 2 keys for rotation
        client.api_key = "key1"
        
        # First call returns 429, second call (after rotation) returns success
        client.session.get.side_effect = [mock_resp_429, mock_resp_ok]
        
        results = client.search_images("nature")
        
        assert client.current_key_index == 1  # Key was rotated
    
    @patch('src.api_client.requests.Session')
    def test_search_videos_success(self, mock_session, client):
        """Test successful video search."""
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "videos": [
                {"id": 1, "video_files": [{"link": "http://example.com/vid.mp4"}]}
            ]
        }
        client.session = mock_session.return_value
        client.session.get.return_value = mock_resp
        
        results = client.search_videos("nature")
        
        assert len(results) == 1
        assert results[0]["id"] == 1
    
    def test_check_rate_limit_reset(self, client):
        """Test rate limit window reset."""
        client.last_reset = 0  # Very old timestamp
        client.request_count = 250  # Over limit
        
        client._check_rate_limit()
        
        assert client.request_count == 0
    
    @patch('time.sleep')
    def test_check_rate_limit_sleep(self, mock_sleep, client):
        """Test that sleep is called when rate limited with single key."""
        client.api_keys = ["single_key"]
        client.current_key_index = 0
        client.request_count = 300  # Over limit
        client.last_reset = 1000
        
        with patch('time.time', return_value=1100):  # Within same hour
            client._check_rate_limit()
        
        mock_sleep.assert_called()
