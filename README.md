# Auto Storyboard Video Creator ðŸŽ¬

<div align="center">

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)]()
[![Python](https://img.shields.io/badge/python-3.8%2B-brightgreen)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.x-000000?logo=flask)]()
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

**AI-powered storyboard video generator â€” transform text and scripts into professional storyboard videos.**

</div>

---

## Overview

Auto Storyboard Video Creator is a Flask web application that automatically generates storyboard videos from text input. It extracts keywords, generates scenes, and compiles them into a cohesive video with optional AI-powered narration.

## Features

- ðŸ“ **Script parsing** â€” Extract keywords and scenes from any text input
- ðŸŽ¨ **Scene generation** â€” Generate visual representations for each storyboard frame
- ðŸ—£ï¸ **Transcription** â€” Automatic speech-to-text for audio input
- ðŸŽ¬ **Video compilation** â€” Combine scenes into a complete storyboard video
- ðŸ¤– **API integration** â€” RESTful API for programmatic access
- ðŸ“¦ **Batch processing** â€” Process multiple scripts in one go
- ðŸŒ **Web interface** â€” User-friendly Flask web UI

## Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | Python, Flask |
| Frontend | HTML, CSS, JavaScript |
| AI APIs | OpenAI / custom endpoints |
| Processing | FFmpeg (video compilation) |
| Container | Docker-ready |

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py

# Open in browser
# http://localhost:5000
```

## Project Structure

```
Auto-Storyboard-Video-Creator/
â”œâ”€â”€ app.py                  # Flask application entry point
â”œâ”€â”€ main.py                 # Core processing logic
â”œâ”€â”€ batch_processor.py      # Batch processing engine
â”œâ”€â”€ config/
â”‚   â””â”€â”€ config.py           # Application configuration
â”œâ”€â”€ src/
â”‚   â”œâ”€â”€ api_client.py       # External API integration
â”‚   â”œâ”€â”€ keyword_extraction.py # Keyword extraction engine
â”‚   â”œâ”€â”€ transcription.py    # Speech-to-text module
â”‚   â””â”€â”€ video_generator.py  # Video generation pipeline
â”œâ”€â”€ templates/
â”‚   â””â”€â”€ index.html          # Web UI template
â”œâ”€â”€ static/
â”‚   â”œâ”€â”€ css/
â”‚   â”‚   â””â”€â”€ style.css
â”‚   â””â”€â”€ js/
â”‚       â””â”€â”€ main.js
â””â”€â”€ requirements.txt
```

## API Usage

```bash
# Submit a script for storyboard generation
curl -X POST http://localhost:5000/api/generate \
  -H "Content-Type: application/json" \
  -d '{"script": "A hero discovers a hidden power..."}'

# Check processing status
curl http://localhost:5000/api/status/{task_id}

# Download generated video
curl http://localhost:5000/api/download/{task_id}
```

## License

MIT â€” see [LICENSE](LICENSE).
