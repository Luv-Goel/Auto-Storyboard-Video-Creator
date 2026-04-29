import os
import uuid
import threading
import logging
import sqlite3
from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Request
from src.video_generator import VideoGenerator
from config.config import OUTPUT_DIR, TEMP_MEDIA_DIR

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VideoCreatorUI")

# Add file handler if LOG_FILE is configured
from config.config import LOG_FILE
if LOG_FILE:
    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(file_handler)
    logging.getLogger().addHandler(file_handler)

app = FastAPI(title="Video Creator UI")

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/output", StaticFiles(directory=OUTPUT_DIR), name="output")
templates = Jinja2Templates(directory="templates")

# SQLite Job Persistence
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "jobs.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS jobs (
            job_id TEXT PRIMARY KEY,
            status TEXT NOT NULL,
            progress INTEGER DEFAULT 0,
            output_path TEXT,
            error TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def save_job(job_id, status, progress, output_path=None, error=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO jobs (job_id, status, progress, output_path, error, updated_at)
        VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    ''', (job_id, status, progress, output_path, error))
    conn.commit()
    conn.close()

def load_job(job_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT job_id, status, progress, output_path, error FROM jobs WHERE job_id = ?', (job_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "job_id": row[0],
            "status": row[1],
            "progress": row[2],
            "output_path": row[3],
            "error": row[4]
        }
    return None

def load_all_jobs():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT job_id, status, progress, output_path, error FROM jobs ORDER BY created_at DESC')
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "job_id": row[0],
            "status": row[1],
            "progress": row[2],
            "output_path": row[3],
            "error": row[4]
        } for row in rows
    ]

init_db()
# Load existing jobs into dict: {job_id: job_dict}
jobs = {job["job_id"]: job for job in load_all_jobs()}

class VideoJob:
    def __init__(self, job_id):
        self.job_id = job_id
        self.status = "initializing"
        self.progress = 0
        self.output_path = None
        self.error = None
        self.save()

    def save(self):
        save_job(self.job_id, self.status, self.progress, self.output_path, self.error)

    def update(self, status=None, progress=None, output_path=None, error=None):
        if status is not None:
            self.status = status
        if progress is not None:
            self.progress = progress
        if output_path is not None:
            self.output_path = output_path
        if error is not None:
            self.error = error
        self.save()

def run_pipeline(
    job_id, 
    audio_path, 
    aspect_ratio, 
    subtitles, 
    subtitle_font=None, 
    subtitle_size=None, 
    subtitle_color=None, 
    subtitle_bg_color=None,
    images_per_minute=None,
    videos_per_minute=None
):
    job = jobs[job_id]
    try:
        job.update(status="Initializing...", progress=5)
        
        def on_progress(message, progress):
            job.update(status=message, progress=progress)
            logger.info(f"Job {job_id}: {progress}% - {message}")

        generator = VideoGenerator(
            aspect_ratio=aspect_ratio, 
            progress_callback=on_progress,
            images_per_minute=images_per_minute,
            videos_per_minute=videos_per_minute
        )
        
        output_path = generator.generate_video(
            audio_path, 
            output_name=f"ui_output_{job_id}",
            subtitles=subtitles,
            subtitle_font=subtitle_font,
            subtitle_size=int(subtitle_size) if subtitle_size else None,
            subtitle_color=subtitle_color,
            subtitle_bg_color=subtitle_bg_color
        )
        
        job.update(
            output_path=os.path.basename(output_path),
            status="Completed successfully!",
            progress=100
        )
        logger.info(f"Job {job_id} completed successfully")
        
    except Exception as e:
        job.update(status="failed", error=str(e))
        logger.error(f"Job {job_id} failed: {e}")

@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/generate")
async def generate(
    background_tasks: BackgroundTasks,
    audio: UploadFile = File(None),
    aspect_ratio: str = Form("16:9"),
    subtitles: bool = Form(False),
    subtitle_font: str = Form(None),
    subtitle_size: str = Form(None),
    subtitle_color: str = Form(None),
    subtitle_bg_color: str = Form(None),
    images_per_minute: int = Form(2),
    videos_per_minute: int = Form(0)
):
    job_id = str(uuid.uuid4())
    
    if audio and audio.filename:
        # Save uploaded audio
        os.makedirs(TEMP_MEDIA_DIR, exist_ok=True)
        audio_path = os.path.join(TEMP_MEDIA_DIR, f"upload_{job_id}_{audio.filename}")
        content = await audio.read()
        if not content:
             # If file is empty, fallback to default
             audio = None
        else:
             with open(audio_path, "wb") as f:
                 f.write(content)
    
    if not audio or not audio.filename:
        # Use default audio
        audio_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "The_Relentless_Engine_of_a_Fragile_Earth-[AudioTrimmer.com].mp3")
        if not os.path.exists(audio_path):
             # Try without AudioTrimmer suffix just in case
             audio_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "The_Relentless_Engine_of_a_Fragile_Earth.mp3")
        
        if not os.path.exists(audio_path):
             raise HTTPException(status_code=400, detail="Default audio file not found on server")
    
    jobs[job_id] = VideoJob(job_id)
    background_tasks.add_task(
        run_pipeline, 
        job_id, 
        audio_path, 
        aspect_ratio, 
        subtitles,
        subtitle_font,
        subtitle_size,
        subtitle_color,
        subtitle_bg_color,
        images_per_minute,
        videos_per_minute
    )
    
    return {"job_id": job_id}

@app.get("/status/{job_id}")
async def status(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    return {
        "status": job.status,
        "progress": job.progress,
        "output_url": f"/output/{job.output_path}" if job.output_path else None,
        "error": job.error
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
