# 🎬 Auto-Storyboard Video Creator (GPU Optimized)

A high-performance, automated video generation pipeline that transforms audio narration into engaging storyboard-style videos. Engineered for high-volume production with NVIDIA GPU acceleration and intelligent media caching.

## 🚀 Key Features

- **⚡ GPU Accelerated Rendering**: Built-in support for NVIDIA NVENC (`h264_nvenc`), delivering up to 4x faster rendering than standard CPU encoders.
- **📦 Batch Processing Engine**: Process hundreds of audio files in parallel with configurable image/video density.
- **🧠 Intelligent Transcription**: Uses `faster-whisper` (tiny/base models) for near-instant offline transcription.
- **🗄️ SQLite Media Cache**: Persistent database caching of stock media. Re-using common keywords results in **instant (<3s)** media lookups.
- **🎨 Dynamic Visuals**: Automatically fetches high-quality stock images and videos from Pexels based on transcription keywords.
- **🎞️ Professional Output**: Generates web-optimized 720p/1080p MP4 files with standard `yuv420p` compatibility.

## 🛠️ Performance Benchmarks

| Setup | Mode | Throughput | Avg. Time / Video |
| :--- | :--- | :--- | :--- |
| **GPU + Hybrid** | Image + Vid Mix | 25 vid/hr | ~141s |
| **GPU + Performance**| Images Only | **208 vid/hr** | **~17s** |

*Benchmarks conducted on a 16-thread CPU with an NVIDIA GTX 1650. (Input Audio duration was 3 mins for all test cases)*

## 📥 Installation

### 1. Requirements
- Python 3.10+
- NVIDIA GPU (optional, but highly recommended for NVENC)
- [FFmpeg](https://ffmpeg.org/) (Included in `/tools`)

### 2. Setup Environment
```bash
git clone https://github.com/yourusername/video-creator.git
cd video-creator
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure API Keys
Create a `.env` file in the root directory:
```bash
PEXELS_API_KEY=your_key_here
```

## 🎮 Usage

### High-Volume Batch Processing
The primary way to use this tool is via the `batch_processor.py`. Place your `.mp3` files in the `input_audio/` folder.

```powershell
# Run 10 videos in GPU mode (3 parallel workers)
python batch_processor.py --mode gpu --count 10 --images 4 --videos 0

# Run in CPU mode (8 parallel workers)
python batch_processor.py --mode cpu --count 5 --images 3 --videos 1
```

### CLI Arguments
- `--mode`: `gpu` (NVENC) or `cpu` (libx264).
- `--count`: Number of files to process from input folder.
- `--images`: Number of images to show per minute of audio.
- `--videos`: Number of video clips to show per minute of audio.

## 📂 Project Structure

```text
├── src/
│   ├── video_generator.py   # Main orchestrator & SQLite Cache
│   ├── transcription.py      # Whisper AI integration
│   ├── keyword_extraction.py # NLP keyword extraction
│   └── api_client.py         # Pexels API integration
├── batch_processor.py        # Parallel processing engine
├── config/
│   └── config.py             # Global settings (FPS, Resolution)
├── input_audio/              # Source your narration files here
├── cache/                    # Persistent SQLite & media cache
└── output/                   # Final rendered videos
```

## 🔧 Optimization Notes
- **MoviePy v1.0.3**: This project uses a specifically tuned version of MoviePy v1.0.3 to bypass performance regressions in newer versions, enabling the 200+ vid/hr throughput.
- **Worker Limits**: GPU mode is capped at 3 parallel workers to respect hardware session limits on consumer NVIDIA cards (like GTX 1650).

## 📄 License
MIT License - See [LICENSE](LICENSE) for details.
