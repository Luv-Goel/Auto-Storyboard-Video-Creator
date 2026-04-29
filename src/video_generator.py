"""
Main Video Generator - Orchestrates the audio-to-storyboard video pipeline.
"""

import os
import time
import random
import shutil
import logging
import sys
import hashlib
import json
import sqlite3
import threading
from typing import List, Dict, Tuple, Callable, Optional, Set
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import moviepy.editor as mpe
from moviepy.config import get_setting
import PIL.Image
# MoviePy v1 compatibility fix for Pillow 10+
if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = PIL.Image.LANCZOS
import requests

from faster_whisper import WhisperModel

from config.config import (
    PEXELS_API_KEYS, TEMP_MEDIA_DIR, OUTPUT_DIR,
    AUDIO_SEGMENT_DURATION, VIDEO_RESOLUTION,
    VIDEO_FPS, PASS_2_MAX_DURATION, FALLBACK_KEYWORDS,
    ASPECT_RATIOS, SUBTITLE_FONT, SUBTITLE_SIZE,
    SUBTITLE_COLOR, SUBTITLE_BG_COLOR, SUBTITLE_POSITION,
    BACKGROUND_MUSIC_PATH, LOG_FILE
)
from src.transcription import TranscriptionService
from src.keyword_extraction import KeywordExtractor
from src.api_client import PexelsClient
from src.exceptions import (
    VideoCreatorError, ConfigurationError, MediaFetchError,
    VideoRenderError, InvalidAudioFileError
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Type aliases
SegmentData = Dict[str, any]
ProgressCallback = Optional[Callable[[str, int], None]]

class MediaCacheDB:
    """SQLite-based media cache tracking."""
    def __init__(self, cache_dir: str):
        self.db_path = os.path.join(cache_dir, "media_cache.db")
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.lock = threading.Lock()
        self._init_db()

    def _init_db(self):
        with self.lock:
            with self.conn:
                self.conn.execute("""
                    CREATE TABLE IF NOT EXISTS cache (
                        query TEXT,
                        media_type TEXT,
                        aspect_ratio TEXT,
                        file_path TEXT,
                        hit_count INTEGER DEFAULT 0,
                        last_accessed DATETIME DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY (query, media_type, aspect_ratio)
                    )
                """)

    def get(self, query: str, media_type: str, aspect_ratio: str) -> Optional[str]:
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT file_path FROM cache WHERE query = ? AND media_type = ? AND aspect_ratio = ?",
                (query, media_type, aspect_ratio)
            )
            row = cursor.fetchone()
            if row and os.path.exists(row[0]):
                self.conn.execute(
                    "UPDATE cache SET hit_count = hit_count + 1, last_accessed = CURRENT_TIMESTAMP WHERE query = ? AND media_type = ? AND aspect_ratio = ?",
                    (query, media_type, aspect_ratio)
                )
                self.conn.commit()
                return row[0]
        return None

    def put(self, query: str, media_type: str, aspect_ratio: str, file_path: str):
        with self.lock:
            with self.conn:
                self.conn.execute(
                    "INSERT OR REPLACE INTO cache (query, media_type, aspect_ratio, file_path, hit_count, last_accessed) VALUES (?, ?, ?, ?, 0, CURRENT_TIMESTAMP)",
                    (query, media_type, aspect_ratio, file_path)
                )

class VideoGenerator:
    """Main orchestrator for audio-to-video storyboard generation."""
    
    def __init__(
        self, 
        pexels_api_keys: Optional[List[str]] = None, 
        aspect_ratio: str = "16:9", 
        progress_callback: ProgressCallback = None,
        images_per_minute: int = 3,
        videos_per_minute: int = 1,
        use_gpu: bool = True
    ) -> None:
        self.api_keys: List[str] = pexels_api_keys or PEXELS_API_KEYS
        self.aspect_ratio: str = aspect_ratio
        self.resolution: Tuple[int, int] = ASPECT_RATIOS.get(aspect_ratio, VIDEO_RESOLUTION)
        self.progress_callback: ProgressCallback = progress_callback
        self.use_gpu: bool = use_gpu
        
        # Optimization: Use 'tiny' model for faster transcription
        self.transcriber: TranscriptionService = TranscriptionService(
            model_size="tiny", 
            device="cpu"
        )
        self.keyword_extractor: KeywordExtractor = KeywordExtractor()
        self.pexels_clients: List[PexelsClient] = []
        
        if self.api_keys:
            for key in self.api_keys:
                try:
                    self.pexels_clients.append(PexelsClient([key]))
                except Exception as e:
                    logger.error(f"Failed to initialize Pexels client: {e}")
        
        self.images_per_minute = int(images_per_minute)
        self.videos_per_minute = int(videos_per_minute)
        
        # Setup FFMPEG
        ffmpeg_local = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                    "tools", "ffmpeg", "ffmpeg-master-latest-win64-gpl", "bin", "ffmpeg.exe")
        if os.path.exists(ffmpeg_local):
            from moviepy.config import change_settings
            change_settings({"FFMPEG_BINARY": ffmpeg_local})
            self.ffmpeg_path = ffmpeg_local
            logger.info(f"Using local FFMPEG: {ffmpeg_local}")
        else:
            self.ffmpeg_path = "ffmpeg"

        # Setup Cache directories
        self.base_cache = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cache")
        self.transcription_cache = os.path.join(self.base_cache, "transcriptions")
        self.media_cache = os.path.join(self.base_cache, "media")
        os.makedirs(self.transcription_cache, exist_ok=True)
        os.makedirs(self.media_cache, exist_ok=True)
        
        self.media_db = MediaCacheDB(self.base_cache)

        self.job_id = hashlib.md5(str(time.time()).encode()).hexdigest()[:8]
        self.temp_dir = os.path.join(TEMP_MEDIA_DIR, f"job_{self.job_id}")
        os.makedirs(self.temp_dir, exist_ok=True)

    def _log_progress(self, message: str, progress: int) -> None:
        logger.info(f"PROGRESS: {progress}% - {message}")
        if self.progress_callback:
            self.progress_callback(message, progress)
    
    def _get_audio_hash(self, audio_path: str) -> str:
        hash_md5 = hashlib.md5()
        with open(audio_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def generate_video(
        self, 
        audio_path: str, 
        output_name: Optional[str] = None, 
        background_music_path: Optional[str] = None
    ) -> str:
        self.current_audio_path: str = audio_path
        start_time: float = time.time()
        
        if not os.path.exists(audio_path):
            raise InvalidAudioFileError(f"Audio file not found: {audio_path}")
        
        if output_name is None:
            output_name = Path(audio_path).stem
        
        total_items_per_min = self.images_per_minute + self.videos_per_minute
        segment_duration = 60.0 / max(1, total_items_per_min)

        # 1. Transcribe (Cached)
        self._log_progress("Transcribing audio...", 10)
        audio_hash = self._get_audio_hash(audio_path)
        cache_file = os.path.join(self.transcription_cache, f"{audio_hash}_{total_items_per_min}.json")
        
        segments = None
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    segments = json.load(f)
            except: pass

        if not segments:
            segments = self.transcriber.transcribe_audio_segments(audio_path, segment_duration=segment_duration)
            try:
                with open(cache_file, 'w') as f:
                    json.dump(segments, f)
            except: pass
        
        # 2. Assign Media Types
        segment_data: List[SegmentData] = self._prepare_segment_data(segments)
        for i, seg in enumerate(segment_data):
            seg["requested_type"] = "image" if (i % max(1, total_items_per_min)) < self.images_per_minute else "video"

        # 3. Fetch Media (Parallel + Cached)
        self._log_progress("Fetching media...", 30)
        self._fetch_unified_media(segment_data)
        
        # 4. Build Video
        self._log_progress("Rendering video...", 70)
        final_path: str = self._build_video_pass(
            segment_data=segment_data, 
            output_name=output_name, 
            background_music_path=background_music_path or BACKGROUND_MUSIC_PATH
        )
        
        self._log_progress(f"Done! Total: {time.time() - start_time:.1f}s", 100)
        return final_path
    
    def _prepare_segment_data(self, segments: List[Dict]) -> List[SegmentData]:
        segment_data: List[SegmentData] = []
        for i, seg in enumerate(segments):
            text: str = seg["text"]
            query = self.keyword_extractor.get_search_query(text) if text.strip() else random.choice(FALLBACK_KEYWORDS)
            segment_data.append({
                "index": i, "start": seg["start"], "end": seg["end"], "duration": seg["end"] - seg["start"],
                "text": text, "query": query, "media_path": None, "media_type": None
            })
        return segment_data
    
    def _fetch_unified_media(self, segment_data: List[SegmentData]) -> None:
        num_clients = len(self.pexels_clients)
        with ThreadPoolExecutor(max_workers=max(1, num_clients)) as executor:
            future_to_seg = {
                executor.submit(
                    self._fetch_stock_media, seg["query"], seg["requested_type"], seg["index"],
                    client=self.pexels_clients[seg["index"] % num_clients] if num_clients > 0 else None
                ): seg for seg in segment_data
            }
            completed = 0
            for future in as_completed(future_to_seg):
                seg = future_to_seg[future]
                try:
                    path = future.result()
                    if path:
                        seg["media_path"] = path
                        seg["media_type"] = seg["requested_type"]
                    else:
                        seg["media_path"] = self._create_color_placeholder(seg["index"])
                        seg["media_type"] = "placeholder"
                except Exception as e:
                    logger.error(f"Fetch failed: {e}")
                    seg["media_path"] = self._create_color_placeholder(seg["index"])
                    seg["media_type"] = "placeholder"
                completed += 1
                self._log_progress(f"Media: {completed}/{len(segment_data)}", 30 + int((completed / len(segment_data)) * 40))

    def _fetch_stock_media(self, query: str, media_type: str, segment_index: int, client=None) -> Optional[str]:
        # Optimization: Media Cache Check (SQLite)
        cached_path = self.media_db.get(query, media_type, self.aspect_ratio)
        ext = ".jpg" if media_type == "image" else ".mp4"
        
        if cached_path and os.path.exists(cached_path):
            logger.debug(f"Media Cache Hit (DB): {query}")
            # Copy to temp for this job
            local_path = os.path.join(self.temp_dir, f"seg_{segment_index:03d}_{media_type}{ext}")
            shutil.copy2(cached_path, local_path)
            return local_path

        # Cache Miss: Download
        pexels_client = client or (self.pexels_clients[0] if self.pexels_clients else None)
        if not pexels_client: return None
        
        try:
            results = pexels_client.search_images(query, per_page=5) if media_type == "image" else pexels_client.search_videos(query, per_page=5)
            if not results: return None
            
            media_info = results[0]
            if media_type == "image":
                url = media_info["src"]["original"]
            else:
                video_files = media_info.get("video_files", [])
                if not video_files: return None
                video_files.sort(key=lambda x: x.get("height", 0), reverse=True)
                url = video_files[0]["link"]
            
            local_path = os.path.join(self.temp_dir, f"seg_{segment_index:03d}_{media_type}{ext}")
            resp = pexels_client.session.get(url, timeout=30)
            resp.raise_for_status()
            with open(local_path, "wb") as f: f.write(resp.content)
            
            # Pre-resize images
            if media_type == "image":
                with PIL.Image.open(local_path) as img:
                    img = img.resize(self.resolution, PIL.Image.LANCZOS)
                    img.save(local_path, quality=85)
            
            # Save to global cache & DB
            cache_key = hashlib.md5(f"{query}_{media_type}_{self.aspect_ratio}".encode()).hexdigest()
            cache_path = os.path.join(self.media_cache, f"{cache_key}{ext}")
            shutil.copy2(local_path, cache_path)
            self.media_db.put(query, media_type, self.aspect_ratio, cache_path)
            
            return local_path
        except Exception as e:
            logger.error(f"Fetch error: {e}")
            return None

    def _create_color_placeholder(self, segment_index: int) -> str:
        color = [(52,73,94),(41,128,185),(46,204,113),(155,89,182),(241,196,15)][segment_index % 5]
        img = PIL.Image.new("RGB", self.resolution, color)
        filepath = os.path.join(self.temp_dir, f"seg_{segment_index:03d}_placeholder.jpg")
        img.save(filepath, "JPEG")
        return filepath
    
    def _build_video_pass(self, segment_data: List[SegmentData], output_name: str, background_music_path: Optional[str] = None) -> str:
        clips = []
        for seg in segment_data:
            path, dur, mtype = seg["media_path"], seg["duration"], seg["media_type"]
            if mtype == "video":
                clip = mpe.VideoFileClip(path).without_audio().resize(height=self.resolution[1])
                if clip.duration < dur: clip = mpe.concatenate_videoclips([clip] * (int(dur/clip.duration)+1))
                clip = clip.subclip(0, dur)
            else:
                clip = mpe.ImageClip(path).set_duration(dur).resize(height=self.resolution[1])
            clips.append(clip)
        
        final_clip = mpe.concatenate_videoclips(clips, method="compose")
        
        audio = mpe.AudioFileClip(self.current_audio_path)
        final_audio = audio.subclip(0, min(final_clip.duration, audio.duration))
        
        if background_music_path and os.path.exists(background_music_path):
            try:
                bgm = mpe.AudioFileClip(background_music_path)
                if bgm.duration < final_clip.duration: bgm = mpe.concatenate_audioclips([bgm] * (int(final_clip.duration/bgm.duration)+1))
                bgm = bgm.subclip(0, final_clip.duration).volumex(0.3)
                final_audio = mpe.CompositeAudioClip([final_audio, bgm])
            except: pass
            
        final_clip = final_clip.set_audio(final_audio)
        output_path = os.path.join(OUTPUT_DIR, f"{output_name}_fixed.mp4")
        
        # GPU Optimization with Compatibility Fixes
        if self.use_gpu:
            codec = "h264_nvenc"
            ffmpeg_params = [
                "-rc", "vbr",
                "-cq", "24",
                "-preset", "p1",
                "-pix_fmt", "yuv420p",        # Standard compatibility
                "-profile:v", "high",         # Standard profile
                "-movflags", "+faststart",    # Web optimized
                "-threads", str(os.cpu_count())
            ]
        else:
            codec = "libx264"
            ffmpeg_params = ["-pix_fmt", "yuv420p"]
        
        final_clip.write_videofile(
            output_path, fps=VIDEO_FPS, codec=codec, audio_codec="aac",
            threads=os.cpu_count(), ffmpeg_params=ffmpeg_params, logger=None
        )
        return output_path

def main() -> int:
    return 0

if __name__ == "__main__":
    main()
