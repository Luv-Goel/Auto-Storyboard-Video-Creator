"""
Keyword extraction module for identifying search terms from transcribed text.

This module provides functionality to extract relevant keywords from text
for use in searching stock media.
"""

import re
from typing import List, Dict, Set


class KeywordExtractor:
    """Extracts keywords from text for media search queries.
    
    Uses a stop-word filtering approach combined with frequency analysis
    to identify the most relevant keywords in a text.
    
    Attributes:
        stop_words: Set of common words to exclude from keywords.
    """
    
    # Common English stop words to filter out
    DEFAULT_STOP_WORDS: Set[str] = {
        "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
        "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
        "being", "have", "has", "had", "do", "does", "did", "will", "would",
        "could", "should", "may", "might", "must", "can", "this", "that",
        "these", "those", "i", "you", "he", "she", "it", "we", "they", "me",
        "him", "her", "us", "them", "my", "your", "his", "its", "our", "their",
        "what", "which", "who", "whom", "where", "when", "why", "how", "all",
        "each", "every", "both", "few", "more", "most", "other", "some", "such",
        "no", "nor", "not", "only", "own", "same", "so", "than", "too", "very",
        "just", "about", "above", "after", "again", "against", "between",
        "during", "before", "under", "while", "through", "above", "below",
        "up", "down", "out", "off", "over", "then", "once"
    }
    
    def __init__(self, custom_stop_words: Set[str] = None) -> None:
        """Initialize the keyword extractor.
        
        Args:
            custom_stop_words: Optional set of additional stop words.
                              Merged with default stop words.
        """
        self.stop_words: Set[str] = self.DEFAULT_STOP_WORDS.copy()
        if custom_stop_words:
            self.stop_words.update(custom_stop_words)
    
    def extract_keywords(self, text: str, max_keywords: int = 5) -> List[str]:
        """Extract keywords from text based on frequency.
        
        Args:
            text: The input text to extract keywords from.
            max_keywords: Maximum number of keywords to return.
            
        Returns:
            List of extracted keywords sorted by frequency.
            
        Example:
            >>> extractor = KeywordExtractor()
            >>> extractor.extract_keywords("The cat sat on the mat")
            ['cat', 'sat', 'mat']
        """
        if not text or text.strip() == "":
            return []
        
        text = text.lower()
        text = re.sub(r'[^a-z\s]', '', text)
        
        words: List[str] = text.split()
        filtered_words: List[str] = [
            word for word in words
            if word not in self.stop_words and len(word) > 2
        ]
        
        word_freq: Dict[str, int] = {}
        for word in filtered_words:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        sorted_keywords: List[tuple] = sorted(
            word_freq.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        keywords: List[str] = [keyword for keyword, freq in sorted_keywords[:max_keywords]]
        
        return keywords[:max_keywords]
    
    def get_search_query(self, text: str, fallback: str = "scenery") -> str:
        """Generate a search query string from text.
        
        Args:
            text: The input text to generate a query from.
            fallback: Fallback query if no keywords are found.
            
        Returns:
            Space-separated string of keywords for use as search query.
            
        Example:
            >>> extractor = KeywordExtractor()
            >>> extractor.get_search_query("Beautiful mountains and rivers")
            'beautiful mountains rivers'
        """
        keywords: List[str] = self.extract_keywords(text)
        if not keywords:
            return fallback
        
        return " ".join(keywords)
