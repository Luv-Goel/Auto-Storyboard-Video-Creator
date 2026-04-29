"""
Unit tests for the keyword extraction module.
"""

import pytest

from src.keyword_extraction import KeywordExtractor


class TestKeywordExtractor:
    """Test cases for KeywordExtractor class."""
    
    def test_init_default(self):
        """Test initialization with default stop words."""
        extractor = KeywordExtractor()
        assert len(extractor.stop_words) > 0
        assert "the" in extractor.stop_words
        assert "and" in extractor.stop_words
    
    def test_init_custom_stop_words(self):
        """Test initialization with custom stop words."""
        custom = {"custom1", "custom2"}
        extractor = KeywordExtractor(custom_stop_words=custom)
        assert "custom1" in extractor.stop_words
        assert "custom2" in extractor.stop_words
        assert "the" in extractor.stop_words  # Default still there
    
    def test_extract_keywords_basic(self, keyword_extractor, sample_text):
        """Test basic keyword extraction."""
        keywords = keyword_extractor.extract_keywords(sample_text)
        
        assert len(keywords) <= 5
        assert all(isinstance(k, str) for k in keywords)
        # Stop words should be filtered out
        assert "the" not in keywords
        assert "in" not in keywords
    
    def test_extract_keywords_empty_string(self, keyword_extractor):
        """Test extraction with empty string."""
        keywords = keyword_extractor.extract_keywords("")
        assert keywords == []
    
    def test_extract_keywords_whitespace(self, keyword_extractor):
        """Test extraction with only whitespace."""
        keywords = keyword_extractor.extract_keywords("   ")
        assert keywords == []
    
    def test_extract_keywords_max_keywords(self, keyword_extractor, sample_text):
        """Test that max_keywords parameter is respected."""
        keywords = keyword_extractor.extract_keywords(sample_text, max_keywords=2)
        assert len(keywords) <= 2
    
    def test_extract_keywords_frequency(self, keyword_extractor):
        """Test that more frequent words are ranked higher."""
        text = "apple banana apple orange banana apple grape"
        keywords = keyword_extractor.extract_keywords(text, max_keywords=3)
        assert keywords[0] == "apple"
    
    def test_extract_keywords_short_words_filtered(self, keyword_extractor):
        """Test that short words (<=2 chars) are filtered out."""
        text = "a ab abc abcd"
        keywords = keyword_extractor.extract_keywords(text)
        assert "a" not in keywords
        assert "ab" not in keywords
    
    def test_get_search_query_with_text(self, keyword_extractor):
        """Test search query generation with valid text."""
        text = "mountains and rivers are beautiful"
        query = keyword_extractor.get_search_query(text)
        assert isinstance(query, str)
        assert len(query) > 0
        assert "mountains" in query or "rivers" in query
    
    def test_get_search_query_empty(self, keyword_extractor):
        """Test search query generation with empty text."""
        query = keyword_extractor.get_search_query("")
        assert query == "scenery"
    
    def test_get_search_query_custom_fallback(self, keyword_extractor):
        """Test search query with custom fallback."""
        query = keyword_extractor.get_search_query("", fallback="custom")
        assert query == "custom"
    
    def test_extract_keywords_returns_list(self, keyword_extractor):
        """Test that extract_keywords always returns a list."""
        result = keyword_extractor.extract_keywords("test")
        assert isinstance(result, list)
    
    def test_get_search_query_returns_string(self, keyword_extractor):
        """Test that get_search_query always returns a string."""
        result = keyword_extractor.get_search_query("test")
        assert isinstance(result, str)
