"""
Pexels API client for fetching stock media.

This module provides a client for interacting with the Pexels API
to search for images and videos for use in video generation.
"""

import os
import time
import logging
from typing import List, Optional, Dict, Any

import requests

from config.config import (
    PEXELS_API_KEYS, PEXELS_RATE_LIMIT, PEXELS_RATE_DELAY
)
from src.exceptions import APIError, RateLimitError, MediaFetchError

logger = logging.getLogger(__name__)


class PexelsClient:
    """Client for interacting with the Pexels API.
    
    Handles authentication, rate limiting, key rotation, and searching
    for images and videos from Pexels.
    
    Attributes:
        api_keys: List of Pexels API keys for rotation.
        current_key_index: Index of the currently active API key.
        api_key: The currently active API key.
        base_url: Base URL for the Pexels API.
        session: Requests session for making HTTP calls.
        request_count: Number of requests made in the current window.
        last_reset: Timestamp of the last rate limit window reset.
    """
    
    def __init__(self, api_keys: Optional[List[str]] = None) -> None:
        """Initialize the Pexels client.
        
        Args:
            api_keys: List of Pexels API keys. If not provided,
                      uses keys from configuration.
                      
        Raises:
            ValueError: If no API keys are provided or found in config.
        """
        self.api_keys: List[str] = api_keys if api_keys is not None else PEXELS_API_KEYS
        if not self.api_keys:
            raise ValueError("No Pexels API keys provided")
        
        self.current_key_index: int = 0
        self.api_key: str = self.api_keys[self.current_key_index]
        
        self.base_url: str = "https://api.pexels.com/v1"
        self.session: requests.Session = requests.Session()
        self._update_session_header()
        
        self.request_count: int = 0
        self.last_reset: float = time.time()
        logger.info(f"Pexels client initialized with {len(self.api_keys)} keys")
    
    def _update_session_header(self) -> None:
        """Update the session headers with the current API key."""
        self.session.headers.update({"Authorization": self.api_key})
        logger.info(f"Switched to Pexels API key ending in ...{self.api_key[-5:]}")
    
    def _rotate_key(self) -> None:
        """Rotate to the next API key in the list."""
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        self.api_key = self.api_keys[self.current_key_index]
        self._update_session_header()
        self.request_count = 0
        self.last_reset = time.time()
    
    def _check_rate_limit(self) -> None:
        """Check and enforce rate limiting.
        
        Rotates API keys or sleeps if rate limits are exceeded.
        """
        current_time: float = time.time()
        if current_time - self.last_reset > 3600:
            self.request_count = 0
            self.last_reset = time.time()
        
        if self.request_count >= PEXELS_RATE_LIMIT:
            if len(self.api_keys) > 1:
                logger.info("Rate limit threshold reached for current key, rotating...")
                self._rotate_key()
            else:
                sleep_time: float = 3600 - (current_time - self.last_reset)
                if sleep_time > 0:
                    logger.warning(f"Rate limit reached, sleeping for {sleep_time:.1f}s")
                    time.sleep(sleep_time)
                    self.request_count = 0
                    self.last_reset = time.time()
        elif self.request_count > 0:
            time.sleep(PEXELS_RATE_DELAY)
    
    def search_images(self, query: str, per_page: int = 10) -> List[Dict[str, Any]]:
        """Search for images on Pexels.
        
        Args:
            query: Search query string.
            per_page: Number of results per page (default: 10).
            
        Returns:
            List of photo objects from the Pexels API.
            
        Raises:
            MediaFetchError: If the API request fails.
        """
        self._check_rate_limit()
        try:
            response: requests.Response = self.session.get(
                "https://api.pexels.com/v1/search",
                params={"query": query, "per_page": per_page, "orientation": "landscape"},
                timeout=30
            )
            
            if response.status_code == 429:
                if len(self.api_keys) > 1:
                    logger.warning("Rate limit hit (429), rotating key...")
                    self._rotate_key()
                    return self.search_images(query, per_page)
                else:
                    logger.warning("Rate limit hit, sleeping for 60 seconds")
                    time.sleep(60)
                    return self.search_images(query, per_page)
            
            response.raise_for_status()
            self.request_count += 1
            data: Dict[str, Any] = response.json()
            return data.get("photos", [])
        except requests.exceptions.RequestException as e:
            logger.error(f"Error searching images: {e}")
            raise MediaFetchError(f"Failed to search images: {e}")
    
    def search_videos(self, query: str, per_page: int = 10) -> List[Dict[str, Any]]:
        """Search for videos on Pexels.
        
        Args:
            query: Search query string.
            per_page: Number of results per page (default: 10).
            
        Returns:
            List of video objects from the Pexels API.
            
        Raises:
            MediaFetchError: If the API request fails.
        """
        self._check_rate_limit()
        try:
            response: requests.Response = self.session.get(
                "https://api.pexels.com/videos/search",
                params={"query": query, "per_page": per_page, "orientation": "landscape"},
                timeout=30
            )
            
            if response.status_code == 429:
                if len(self.api_keys) > 1:
                    logger.warning("Rate limit hit (429), rotating key...")
                    self._rotate_key()
                    return self.search_videos(query, per_page)
                else:
                    logger.warning("Rate limit hit, sleeping for 60 seconds")
                    time.sleep(60)
                    return self.search_videos(query, per_page)
            
            response.raise_for_status()
            self.request_count += 1
            data: Dict[str, Any] = response.json()
            return data.get("videos", [])
        except requests.exceptions.RequestException as e:
            logger.error(f"Error searching videos: {e}")
            raise MediaFetchError(f"Failed to search videos: {e}")