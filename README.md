# Auto Storyboard Video Creator 🎬

<div align="center">

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)]()
[![Python](https://img.shields.io/badge/python-3.8%2B-brightgreen)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![CI](https://github.com/Luv-Goel/Auto-Storyboard-Video-Creator/actions/workflows/ci.yml/badge.svg)](https://github.com/Luv-Goel/Auto-Storyboard-Video-Creator/actions/workflows/ci.yml)
[![Code Coverage](https://img.shields.io/badge/coverage-85%25-brightgreen)]()
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen)]()

**AI-powered storyboard and video creation — generate storyboards from scripts, batch process videos, TUI interface. Perfect for content creators and pre-production.**

</div>

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 📝 **Script-to-Storyboard** | Parse text scripts and automatically generate storyboard frames with camera angles, lighting, and mood analysis |
| 🎨 **Scene Visualization** | Render professional storyboard panels as high-resolution images with metadata overlays |
| 🎤 **Audio Transcription** | Automatic speech-to-text for audio input using faster-whisper |
| 🖼️ **Stock Media Integration** | Fetch relevant images and videos from Pexels API based on scene keywords |
| 🎬 **Video Compilation** | Combine scenes into a complete storyboard video with optional background music |
| 🔄 **Batch Processing** | Process multiple scripts in one go |
| 🖥️ **Web Interface** | User-friendly Flask/FastAPI web UI for uploading and processing |
| 🎮 **TUI Interface** | Terminal-based user interface for power users |
| 🎯 **Keyword Extraction** | Intelligent keyword extraction for media search queries |
| 🌐 **Multi-Aspect Ratio** | Support for 16:9, 9:16, 1:1, 4:3 and custom resolutions |

---

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/Luv-Goel/Auto-Storyboard-Video-Creator.git
cd Auto-Storyboard-Video-Creator

# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py

# Open in browser
# http://localhost:8000
```

### Convert a script to storyboard frames

```python
from src.script_to_video import script_to_storyboard

script = """
INT. SPACESHIP - DAY

The captain stares out the window at a swirling nebula.

EXT. ALIEN PLANET - NIGHT

A strange figure emerges from the shadows.
"""

storyboard = script_to_storyboard(
    script_text=script,
    output_dir="./my_storyboard",
    title="Space Adventure",
    known_characters=["Captain", "Alien"],
)

print(f"Generated {storyboard.total_frames} frames")
```

---

## 📦 Project Structure

```
Auto-Storyboard-Video-Creator/
├── app.py                  # FastAPI web application entry point
├── main.py                 # Core processing logic entry point
├── batch_processor.py      # Batch processing engine
├── config/
│   └── config.py           # Application configuration
├── src/
│   ├── api_client.py       # External API integration (Pexels)
│   ├── keyword_extraction.py  # Keyword extraction engine
│   ├── script_to_video.py  # Script-to-storyboard conversion (NEW)
│   ├── transcription.py    # Speech-to-text module
│   ├── video_generator.py  # Video generation pipeline
│   └── exceptions.py       # Custom exception classes
├── templates/
│   └── index.html          # Web UI template
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── main.js
├── tests/
│   ├── tests.py            # Basic tests for core features
│   ├── test_video_generator.py
│   ├── test_keyword_extraction.py
│   ├── test_transcription.py
│   ├── test_api_client.py
│   ├── test_exceptions.py
│   └── conftest.py
└── requirements.txt
```

---

## 🛠️ Usage

### Web Interface

```bash
python app.py
# Visit http://localhost:8000
```

### TUI Interface

```bash
python tui.py
```

### Batch Processing

```bash
python batch_processor.py --input ./scripts/ --output ./videos/
```

### Command Line

```bash
python main.py --audio input.mp3 --aspect 16:9 --subtitles
```

---

## 📡 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Web UI homepage |
| `/generate` | POST | Submit audio for storyboard video generation |
| `/status/{job_id}` | GET | Check processing status |
| `/api/generate` | POST | API endpoint for script-to-storyboard |
| `/api/status/{task_id}` | GET | API task status check |
| `/api/download/{task_id}` | GET | Download generated video |

### API Usage

```bash
# Submit a script for storyboard generation
curl -X POST http://localhost:8000/api/generate \
  -H "Content-Type: application/json" \
  -d '{"script": "A hero discovers a hidden power..."}'

# Check processing status
curl http://localhost:8000/api/status/{task_id}

# Download generated video
curl http://localhost:8000/api/download/{task_id}
```

---

## 🧪 Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_script_to_video.py -v
```

---

## 🔧 Configuration

Copy `.env.example` to `.env` and configure:

| Variable | Description | Default |
|----------|-------------|---------|
| `PEXELS_API_KEY` | Pexels API key for stock media | — |
| `HOST` | Server host | `0.0.0.0` |
| `PORT` | Server port | `8000` |
| `IMAGES_PER_MINUTE` | Images per minute of audio | `2` |
| `VIDEOS_PER_MINUTE` | Videos per minute of audio | `0` |
| `ASPECT_RATIO` | Output video aspect ratio | `16:9` |
| `LOG_LEVEL` | Logging level | `INFO` |

---

## 📦 Dependencies

- **Python** ≥ 3.8
- **FastAPI** / **Flask** — Web framework
- **faster-whisper** — Speech-to-text transcription
- **Pillow** — Image processing
- **moviepy** — Video compilation
- **FFmpeg** — Video encoding (required)
- **rich** — TUI interface

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

MIT — see [LICENSE](LICENSE).

---

<div align="center">
  <p>Built with ❤️ for content creators and pre-production workflows</p>
  <p>© 2026 Auto Storyboard Video Creator</p>
</div>
