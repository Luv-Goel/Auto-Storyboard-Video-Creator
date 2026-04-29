"""
Configuration module for Video Creator application.

Loads configuration from environment variables and provides
default values for all settings.
"""

import os
import logging
from typing import List, Tuple, Dict, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize logger
logger = logging.getLogger(__name__)


def _get_env_int(key: str, default: int) -> int:
    """Get an integer value from environment variable.
    
    Args:
        key: Environment variable name.
        default: Default value if not found or invalid.
        
    Returns:
        Integer value from env or default.
    """
    value: Optional[str] = os.getenv(key)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _get_env_float(key: str, default: float) -> float:
    """Get a float value from environment variable.
    
    Args:
        key: Environment variable name.
        default: Default value if not found or invalid.
        
    Returns:
        Float value from env or default.
    """
    value: Optional[str] = os.getenv(key)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default


# ─── API Keys ───────────────────────────────────────────────────────

PEXELS_API_KEYS: List[str] = [
    os.getenv(f"PEXELS_API_KEY_{i}") for i in range(1, 11)
]
PEXELS_API_KEYS = [k for k in PEXELS_API_KEYS if k and k != "your_api_key_here"]

# ─── Media Frequency Settings ───────────────────────────────────────
# Number of images/videos to aim for per minute of audio
DEFAULT_IMAGES_PER_MINUTE: int = _get_env_int("IMAGES_PER_MINUTE", 2)
DEFAULT_VIDEOS_PER_MINUTE: int = _get_env_int("VIDEOS_PER_MINUTE", 0)

if not PEXELS_API_KEYS:
    # Fallback to single key if exists
    single_key: Optional[str] = os.getenv("PEXELS_API_KEY")
    if single_key and single_key != "your_api_key_here":
        PEXELS_API_KEYS = [single_key]
    else:
        logger.warning("No valid PEXELS_API_KEY found in .env. Pexels API features will be disabled.")
        PEXELS_API_KEYS = []

# For backward compatibility
PEXELS_API_KEY: Optional[str] = PEXELS_API_KEYS[0] if PEXELS_API_KEYS else None

# ─── Unsplash API (Phase 2) ────────────────────────────────────────

UNSPLASH_API_KEY: Optional[str] = os.getenv("UNSPLASH_API_KEY")
UNSPLASH_ACCESS_KEY: Optional[str] = os.getenv("UNSPLASH_ACCESS_KEY")

# ─── Pixabay API (Phase 2) ────────────────────────────────────────

PIXABAY_API_KEY: Optional[str] = os.getenv("PIXABAY_API_KEY")

# ─── Directories ────────────────────────────────────────────────────

BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMP_MEDIA_DIR: str = os.path.join(BASE_DIR, "temp_media")
OUTPUT_DIR: str = os.path.join(BASE_DIR, "output")
CACHE_DIR: str = os.path.join(BASE_DIR, ".cache")

# Ensure directories exist
os.makedirs(TEMP_MEDIA_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)

# ─── Audio Processing ───────────────────────────────────────────────

AUDIO_SEGMENT_DURATION: int = _get_env_int("AUDIO_SEGMENT_DURATION", 30)
SAMPLE_RATE: int = _get_env_int("SAMPLE_RATE", 16000)
BACKGROUND_MUSIC_PATH: Optional[str] = os.getenv("BACKGROUND_MUSIC_PATH", None)

# ─── Video Settings ─────────────────────────────────────────────────

VIDEO_RESOLUTION: Tuple[int, int] = (1280, 720)
VIDEO_FPS: int = _get_env_int("VIDEO_FPS", 30)
VIDEO_CODEC: str = os.getenv("VIDEO_CODEC", "libx264")
AUDIO_CODEC: str = os.getenv("AUDIO_CODEC", "aac")
VIDEO_PRESET: str = os.getenv("VIDEO_PRESET", "medium")
VIDEO_THREADS: int = _get_env_int("VIDEO_THREADS", 2)

# ─── Aspect Ratios ─────────────────────────────────────────────────

ASPECT_RATIOS: Dict[str, Tuple[int, int]] = {
    "16:9": (1280, 720),
    "9:16": (720, 1280),
    "1:1": (720, 720),
    "4:3": (960, 720),
}

# ─── Subtitle Settings ──────────────────────────────────────────────

SUBTITLE_FONT: str = os.getenv("SUBTITLE_FONT", "arial.ttf")
SUBTITLE_SIZE: int = _get_env_int("SUBTITLE_SIZE", 48)
SUBTITLE_COLOR: str = os.getenv("SUBTITLE_COLOR", "white")
SUBTITLE_BG_COLOR: str = os.getenv("SUBTITLE_BG_COLOR", "black")
SUBTITLE_POSITION: Tuple[str, str] = ("center", "bottom")
SUBTITLE_WRAP_WIDTH: float = _get_env_float("SUBTITLE_WRAP_WIDTH", 0.8)

# ─── Pass Conditions ────────────────────────────────────────────────

PASS_2_MAX_DURATION: int = _get_env_int("PASS_2_MAX_DURATION", 420)

# ─── Fallback Keywords ──────────────────────────────────────────────

FALLBACK_KEYWORDS: List[str] = [
    "nature", "landscape", "ambient", "scenery",
    "abstract", "background", "texture"
]

# ─── Pexels API Settings ───────────────────────────────────────────

PEXELS_API_URL: str = "https://api.pexels.com/v1"
PEXELS_RATE_LIMIT: int = _get_env_int("PEXELS_RATE_LIMIT", 200)
PEXELS_RATE_DELAY: float = _get_env_float("PEXELS_RATE_DELAY", 18.0)

# ─── Request Settings ──────────────────────────────────────────────

REQUEST_TIMEOUT: int = _get_env_int("REQUEST_TIMEOUT", 30)
MAX_RETRIES: int = _get_env_int("MAX_RETRIES", 3)
RETRY_BACKOFF_FACTOR: float = _get_env_float("RETRY_BACKOFF_FACTOR", 2.0)

# ─── Logging ───────────────────────────────────────────────────────

LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE: Optional[str] = os.getenv("LOG_FILE", None)

# ─── Web UI Settings ────────────────────────────────────────────────

HOST: str = os.getenv("HOST", "0.0.0.0")
PORT: int = _get_env_int("PORT", 8000)
DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

# ─── Cache Settings ────────────────────────────────────────────────

ENABLE_CACHE: bool = os.getenv("ENABLE_CACHE", "true").lower() == "true"
CACHE_TTL: int = _get_env_int("CACHE_TTL", 86400)  # 24 hours
