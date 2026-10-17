import os, shutil, subprocess, tempfile, uuid
from pathlib import Path
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

app = FastAPI(title="FLAVOX AI Video Enhancer API", version="0.2.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=False,
                   allow_methods=["*"], allow_headers=["*"])
BASE_DIR = Path(os.getenv("FLAVOX_WORK_DIR", tempfile.gettempdir())) / "flavox-ai"
BASE_DIR.mkdir(parents=True, exist_ok=True)
MAX_UPLOAD_BYTES = int(os.getenv("FLAVOX_MAX_UPLOAD_BYTES", str(500 * 1024 * 1024)))
ALLOWED_EXTS = {".mp4", ".mov", ".mkv", ".webm", ".avi", ".m4v"}

@app.get("/health")
def health():
    return {"ok": True, "service": "FLAVOX AI Video Enhancer API",
            "processing": "FFmpeg filters; AI model integration is a separate step"}

@app.post("/api/enhance")
async def enhance(file: UploadFile = File(...), scale: int = Form(2),
                  sharpen: bool = Form(True), denoise: bool = Form(True),
                  fps: int = Form(0)):
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        raise HTTPException(500, "FFmpeg/ffprobe not found on PATH.")
    ext = Path(file.filename or "video.mp4").suffix.lower()
    if ext not in ALLOWED_EXTS:
        raise HTTPException(400, "Unsupported video format.")
    if scale not in (1, 2, 4) or fps not in (0, 30, 60):
        raise HTTPException(400, "Invalid scale or FPS.")
    job_dir = BASE_DIR / uuid.uuid4().hex
    job_dir.mkdir(parents=True, exist_ok=True)
    src, dst = job_dir / f"input{ext}", job_dir / "FLAVOX_AI_Enhanced.mp4"
    size = 0
    try:
        with src.open("wb") as out:
            while chunk := await file.read(1024 * 1024):
                size += len(chunk)
                if size > MAX_UPLOAD_BYTES:
                    raise HTTPException(413, f"Upload limit is {MAX_UPLOAD_BYTES // (1024*1024)} MB.")
                out.write(chunk)
        filters = []
        if scale > 1:
            filters.append(f"scale=trunc(iw*{scale}/2)*2:trunc(ih*{scale}/2)*2:flags=lanczos")
        if denoise: filters.append("hqdn3d=1.5:1.5:6:6")
        if sharpen: filters.append("unsharp=5:5:0.7:3:3:0.0")
        if fps: filters.append(f"fps={fps}")
        cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(src),
               "-vf", ",".join(filters) if filters else "null",
               "-c:v", "libx264", "-preset", "medium", "-crf", "18",
               "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
               "-movflags", "+faststart", str(dst)]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
        except subprocess.TimeoutExpired:
            raise HTTPException(504, "Processing timed out. Try a shorter video.")
        if result.returncode or not dst.exists():
            raise HTTPException(422, (result.stderr or "FFmpeg failed")[-1200:])
        # FileResponse streams the result. Production needs a scheduled cleanup job.
        return FileResponse(str(dst), media_type="video/mp4", filename="FLAVOX_AI_Enhanced.mp4")
    finally:
        await file.close()
