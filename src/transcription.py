"""
Transcription module using faster-whisper for local audio transcription.

This module provides speech-to-text functionality using the faster-whisper
library, which is a fast implementation of OpenAI's Whisper model.
"""

import os
import logging
from typing import List, Dict, Optional, Callable

from faster_whisper import WhisperModel

# Add parent to path for config
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.config import AUDIO_SEGMENT_DURATION
from src.exceptions import TranscriptionError

logger = logging.getLogger(__name__)


class TranscriptionService:
    """Service for transcribing audio files using faster-whisper.
    
    Provides methods for transcribing audio and segmenting the transcription
    into fixed-duration segments.
    
    Attributes:
        model_size: Size of the Whisper model to use (e.g., "base", "medium").
        device: Device to run the model on ("cpu" or "cuda").
        model: The loaded WhisperModel instance.
    """
    
    def __init__(self, model_size: str = "base", device: str = "cpu") -> None:
        """Initialize the transcription service.
        
        Args:
            model_size: Whisper model size. Options: "tiny", "base", "small",
                       "medium", "large". Larger models are more accurate
                       but slower.
            device: Device to run inference on. Use "cuda" for GPU
                    acceleration if available.
        """
        self.model_size: str = model_size
        self.device: str = device
        self.model: Optional[WhisperModel] = None
        logger.info(f"Initializing faster-whisper model ({model_size}) on {device}")
    
    def load_model(self) -> None:
        """Load the Whisper model into memory.
        
        Raises:
            TranscriptionError: If the model fails to load.
        """
        if self.model is None:
            try:
                self.model = WhisperModel(self.model_size, device=self.device)
                logger.info("Transcription model loaded successfully")
            except Exception as e:
                raise TranscriptionError(f"Failed to load Whisper model: {e}")
    
    def transcribe_audio(
        self, 
        audio_path: str, 
        progress_callback: Optional[Callable] = None
    ) -> List[Dict[str, float]]:
        """Transcribe an audio file to text segments.
        
        Args:
            audio_path: Path to the audio file to transcribe.
            progress_callback: Optional callback function to report progress.
                              Signature: func(message: str, progress: int).
                              
        Returns:
            List of segment dictionaries with keys: "start", "end", "text".
            
        Raises:
            TranscriptionError: If transcription fails.
            FileNotFoundError: If the audio file doesn't exist.
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        self.load_model()
        segments: List[Dict[str, float]] = []
        
        logger.info(f"Transcribing audio file: {audio_path}")
        try:
            result = self.model.transcribe(
                audio_path,
                word_timestamps=False,
                language=None,
                task="transcribe"
            )
            # result is a tuple: (segments_generator, info)
            segments_generator, info = result
            
            for segment in segments_generator:
                segments.append({
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text.strip()
                })
            
            logger.info(f"Transcription complete. Generated {len(segments)} segments")
            return segments
            
        except Exception as e:
            raise TranscriptionError(f"Transcription failed: {e}")
    
    def transcribe_audio_segments(
        self, 
        audio_path: str, 
        segment_duration: Optional[int] = None
    ) -> List[Dict[str, float]]:
        """Transcribe audio and segment into fixed-duration chunks.
        
        Args:
            audio_path: Path to the audio file to transcribe.
            segment_duration: Duration of each segment in seconds.
                            Defaults to AUDIO_SEGMENT_DURATION from config.
                            
        Returns:
            List of segment dictionaries with fixed durations and combined text.
        """
        if segment_duration is None:
            segment_duration = AUDIO_SEGMENT_DURATION
        
        all_segments: List[Dict[str, float]] = self.transcribe_audio(audio_path)
        if not all_segments:
            return []
        
        total_duration: float = all_segments[-1]["end"]
        num_segments: int = int(total_duration / segment_duration) + 1
        
        rigid_segments: List[Dict[str, float]] = []
        for i in range(num_segments):
            start_time: float = i * segment_duration
            end_time: float = (i + 1) * segment_duration
            
            bucket_text: str = ""
            for seg in all_segments:
                if seg["end"] > start_time and seg["start"] < end_time:
                    bucket_text += " " + seg["text"]
            
            rigid_segments.append({
                "start": start_time,
                "end": end_time,
                "text": bucket_text.strip()
            })
        
        logger.info(f"Created {len(rigid_segments)} rigid segments")
        return rigid_segments