"""
Test script for the Audio-to-Storyboard Video Generator.
"""

import os
import sys
import tempfile
import wave
import struct
import math
import logging

# Add src to path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from src.transcription import TranscriptionService
from src.keyword_extraction import KeywordExtractor
from src.api_client import PexelsClient
from src.video_generator import VideoGenerator

from config.config import *

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def generate_test_audio(filename: str, duration: int = 120, frequency: float = 440.0):
    """
    Generate a simple test audio file (sine wave) for testing.
    
    Args:
        filename: Output WAV file path
        duration: Duration in seconds
        frequency: Sine wave frequency (Hz)
    """
    sample_rate = 22050
    amplitude = 0.5
    
    logger.info(f"Generating test audio: {duration}s at {frequency}Hz")
    
    with wave.open(filename, 'w') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        
        for i in range(int(duration * sample_rate)):
            value = int(amplitude * 32767 * math.sin(2 * math.pi * frequency * i / sample_rate))
            data = struct.pack('<h', value)
            wav_file.writeframes(data)
    
    logger.info(f"Test audio saved: {filename}")
    return filename


def test_transcription():
    """Test the transcription service."""
    logger.info("="*60)
    logger.info("TEST 1: Transcription Service")
    logger.info("="*60)
    
    # Generate a short test audio
    test_audio = "test_audio.wav"
    generate_test_audio(test_audio, duration=10)
    
    # Initialize transcriber
    transcriber = TranscriptionService(model_size="base", device="cpu")
    
    # Test transcription
    logger.info("Transcribing...")
    segments = transcriber.transcribe_audio_segments(test_audio, segment_duration=30)
    
    logger.info(f"Transcription complete: {len(segments)} segments")
    for seg in segments:
        logger.info(f"  [{seg['start']:.1f}-{seg['end']:.1f}s]: {seg['text']}")
    
    # Cleanup
    os.remove(test_audio)
    logger.info("✓ Transcription test passed\n")
    return True


def test_keyword_extraction():
    """Test keyword extraction."""
    logger.info("="*60)
    logger.info("TEST 2: Keyword Extraction")
    logger.info("="*60)
    
    extractor = KeywordExtractor()
    
    test_cases = [
        "The quick brown fox jumps over the lazy dog in the forest",
        "Machine learning and artificial intelligence are transforming technology",
        "",
        "Silent segment with no words spoken",
    ]
    
    for text in test_cases:
        query = extractor.get_search_query(text)
        keywords = extractor.extract_keywords(text)
        logger.info(f"Text: '{text[:50]}...'")
        logger.info(f"  Query: '{query}'")
        logger.info(f"  Keywords: {keywords}")
    
    logger.info("✓ Keyword extraction test passed\n")
    return True


def test_pexels_client():
    """Test Pexels API client."""
    logger.info("="*60)
    logger.info("TEST 3: Pexels API Client")
    logger.info("="*60)
    
    try:
        if not PEXELS_API_KEY or PEXELS_API_KEY == "your_api_key_here":
            logger.warning("PEXELS_API_KEY not configured, skipping API test")
            logger.info("  Set PEXELS_API_KEY in .env to enable\n")
            return True
    except:
        logger.warning("PEXELS_API_KEY not configured, skipping API test\n")
        return True
    
    try:
        client = PexelsClient(PEXELS_API_KEY)
        
        # Test image search
        logger.info("Testing image search for 'nature'...")
        images = client.search_images("nature", per_page=3)
        logger.info(f"  Found {len(images)} images")
        if images:
            logger.info(f"  First: {images[0]['photographer']} - {images[0]['url']}")
        
        # Test video search
        logger.info("Testing video search for 'ocean'...")
        videos = client.search_videos("ocean", per_page=3)
        logger.info(f"  Found {len(videos)} videos")
        if videos:
            logger.info(f"  First: {videos[0]['user']['name']} - {videos[0]['url']}")
        
        logger.info("✓ Pexels client test passed\n")
        return True
        
    except Exception as e:
        logger.error(f"Pexels test failed: {e}")
        return False


def test_full_pipeline():
    """Test the full video generation pipeline (without actual video rendering)."""
    logger.info("="*60)
    logger.info("TEST 4: Full Pipeline (Dry Run)")
    logger.info("="*60)
    
    try:
        from src.video_generator import VideoGenerator
        
        # Create generator
        generator = VideoGenerator()
        logger.info("VideoGenerator initialized")
        
        # Test with a very short silent audio
        test_audio = "test_silent.wav"
        generate_test_audio(test_audio, duration=5)
        
        logger.info("Running pipeline steps...")
        
        # Step 1: Transcribe
        segments = generator.transcriber.transcribe_audio_segments(
            test_audio, 
            segment_duration=30
        )
        logger.info(f"  Transcribed: {len(segments)} segments")
        
        # Step 2: Extract keywords for each segment
        for seg in segments:
            query = generator.keyword_extractor.get_search_query(seg['text'])
            logger.info(f"  Segment query: '{query}'")
        
        # Step 3: Test media fetching (if API key available)
        if generator.pexels_client:
            logger.info("  Testing media fetch...")
            media = generator._fetch_stock_media("test", "image", 0)
            if media:
                logger.info(f"    Media fetched: {media}")
                os.remove(media)
        
        # Cleanup
        os.remove(test_audio)
        
        logger.info("✓ Full pipeline test passed\n")
        return True
        
    except Exception as e:
        logger.error(f"Pipeline test failed: {e}", exc_info=True)
        return False


def test_aspect_ratios():
    """Test aspect ratio initialization."""
    logger.info("="*60)
    logger.info("TEST 5: Aspect Ratio & Subtitles")
    logger.info("="*60)
    
    test_cases = [
        ("16:9", (1920, 1080)),
        ("9:16", (1080, 1920)),
        ("1:1", (1080, 1080)),
    ]
    
    for ar, expected_res in test_cases:
        generator = VideoGenerator(aspect_ratio=ar)
        logger.info(f"Testing {ar}: Resolution {generator.resolution}")
        if generator.resolution != expected_res:
            logger.error(f"  FAILED: Expected {expected_res}, got {generator.resolution}")
            return False
        logger.info(f"  ✓ {ar} passed")
        
    logger.info("✓ Aspect ratio test passed\n")
    return True


def main():
    """Run all tests."""
    logger.info("\n" + "="*60)
    logger.info("VIDEO GENERATOR TEST SUITE")
    logger.info("="*60 + "\n")
    
    results = []
    
    try:
        results.append(("Transcription", test_transcription()))
    except Exception as e:
        logger.error(f"Transcription test failed: {e}")
        results.append(("Transcription", False))
    
    try:
        results.append(("Keyword Extraction", test_keyword_extraction()))
    except Exception as e:
        logger.error(f"Keyword test failed: {e}")
        results.append(("Keyword Extraction", False))
    
    try:
        results.append(("Pexels Client", test_pexels_client()))
    except Exception as e:
        logger.error(f"Pexels test failed: {e}")
        results.append(("Pexels Client", False))
    
    try:
        results.append(("Full Pipeline", test_full_pipeline()))
    except Exception as e:
        logger.error(f"Pipeline test failed: {e}")
        results.append(("Full Pipeline", False))

    try:
        results.append(("Aspect Ratios", test_aspect_ratios()))
    except Exception as e:
        logger.error(f"Aspect ratio test failed: {e}")
        results.append(("Aspect Ratios", False))
    
    # Summary
    logger.info("="*60)
    logger.info("TEST SUMMARY")
    logger.info("="*60)
    for name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        logger.info(f"{name}: {status}")
    
    all_passed = all(r[1] for r in results)
    logger.info("="*60)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
