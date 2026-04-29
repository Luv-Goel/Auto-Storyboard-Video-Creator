import os
import time
import logging
import argparse
from typing import List
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

from src.video_generator import VideoGenerator
from config.config import PEXELS_API_KEYS

# --- BATCH CONFIGURATION ---
INPUT_DIR = "input_audio"  # Place all your .mp3 files here
ASPECT_RATIO = "16:9"
# ---------------------------

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [BATCH] - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def process_single_video(audio_file: str, use_gpu: bool, images_per_min: int, videos_per_min: int):
    """Worker function for parallel processing."""
    try:
        audio_path = os.path.join(INPUT_DIR, audio_file)
        mode_suffix = "gpu" if use_gpu else "cpu"
        output_name = f"batch_{mode_suffix}_{Path(audio_file).stem}"
        
        logger.info(f">>> Starting {mode_suffix.upper()} worker for: {audio_file}")
        
        generator = VideoGenerator(
            aspect_ratio=ASPECT_RATIO,
            images_per_minute=images_per_min,
            videos_per_minute=videos_per_min,
            use_gpu=use_gpu
        )
        
        start_time = time.time()
        final_path = generator.generate_video(
            audio_path=audio_path,
            output_name=output_name
        )
        duration = time.time() - start_time
        
        return {
            "status": "SUCCESS",
            "file": audio_file,
            "duration": duration,
            "path": final_path
        }
    except Exception as e:
        logger.error(f"Worker failed for {audio_file}: {e}")
        return {
            "status": "FAILED",
            "file": audio_file,
            "error": str(e)
        }

def run_batch(mode: str, count: int, images: int, videos: int):
    """Main orchestrator for the batch queue."""
    if not os.path.exists(INPUT_DIR):
        os.makedirs(INPUT_DIR)
        print(f"Created '{INPUT_DIR}' folder. Please add your .mp3 files there and restart.")
        return

    audio_files = [f for f in os.listdir(INPUT_DIR) if f.lower().endswith(('.mp3', '.wav', '.m4a'))]
    audio_files = audio_files[:count]
    
    if not audio_files:
        print(f"No audio files found in '{INPUT_DIR}'.")
        return

    use_gpu = mode.lower() == "gpu"
    # Optimization: Increased concurrency
    # GPU: 3 workers (GTX 1650 hardware limit)
    # CPU: 8 workers (50% of available threads)
    max_workers = 3 if use_gpu else 8

    print(f"\n" + "="*50)
    print(f"--- BATCH PROCESSOR: {mode.upper()} MODE ---")
    print(f"Processing {len(audio_files)} files.")
    print(f"Parallel workers: {max_workers}")
    print(f"Settings: {images} img/min, {videos} vid/min, 720p")
    print(f"="*50 + "\n")

    start_time = time.time()
    results = []
    
    # Using ProcessPoolExecutor for true parallelism
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(process_single_video, f, use_gpu, images, videos) for f in audio_files]
        
        for future in as_completed(futures):
            res = future.result()
            results.append(res)
            if res["status"] == "SUCCESS":
                print(f"[OK] {res['file']} finished in {res['duration']:.1f}s")
            else:
                print(f"[FAIL] {res['file']} failed: {res['error']}")

    total_time = time.time() - start_time
    
    print(f"\n" + "-"*50)
    print(f"--- {mode.upper()} BATCH COMPLETE ---")
    print(f"Total time for {len(audio_files)} videos: {total_time:.2f} seconds ({total_time/60:.2f} minutes)")
    if results:
        success_count = sum(1 for r in results if r["status"] == "SUCCESS")
        avg_time = total_time / len(audio_files)
        print(f"Success: {success_count}/{len(audio_files)}")
        print(f"Average time per video: {avg_time:.2f} seconds")
    print("-"*50 + "\n")
    
    return total_time

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Batch video processor with GPU/CPU comparison support.")
    parser.add_argument("--mode", choices=["gpu", "cpu"], default="gpu", help="Rendering mode (gpu or cpu)")
    parser.add_argument("--count", type=int, default=5, help="Number of videos to process")
    parser.add_argument("--images", type=int, default=3, help="Images per minute")
    parser.add_argument("--videos", type=int, default=1, help="Videos per minute")
    
    args = parser.parse_args()
    run_batch(args.mode, args.count, args.images, args.videos)
