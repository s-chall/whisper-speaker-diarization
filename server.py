"""FastAPI server that wraps the transcription pipeline for the React UI."""

from __future__ import annotations

import os
import shutil
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Optional

from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from audio_handler import load_audio
from diarizer import diarize, load_diarization_pipeline, normalize_speaker_labels
from formatter import save_pdf
from pipeline import assign_speakers, merge_consecutive
from transcriber import load_whisper_model, transcribe

load_dotenv()

AUDIO_DIR = "audio"
TRANSCRIPT_DIR = "transcripts"
UPLOAD_DIR = "uploads"
MODEL_CHOICES = {"tiny", "base", "small", "medium", "large"}

os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(TRANSCRIPT_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)


@dataclass
class Job:
    id: str
    status: str = "queued"
    stage: str = "queued"
    progress: float = 0.0
    message: str = ""
    error: Optional[str] = None
    transcript: list[dict] = field(default_factory=list)
    speakers: list[str] = field(default_factory=list)
    pdf_path: Optional[str] = None
    base_name: str = "transcript"
    created_at: float = field(default_factory=time.time)


JOBS: dict[str, Job] = {}
JOBS_LOCK = threading.Lock()

WHISPER_MODELS: dict[str, object] = {}
DIAR_PIPELINE = None
MODEL_LOCK = threading.Lock()


def _get_whisper_model(size: str):
    with MODEL_LOCK:
        if size not in WHISPER_MODELS:
            WHISPER_MODELS[size] = load_whisper_model(size)
        return WHISPER_MODELS[size]


def _get_diarization_pipeline():
    global DIAR_PIPELINE
    with MODEL_LOCK:
        if DIAR_PIPELINE is None:
            hf_token = os.getenv("HF_TOKEN")
            if not hf_token:
                raise RuntimeError(
                    "HF_TOKEN is not set. Add it to your .env file. "
                    "Model access required at "
                    "https://huggingface.co/pyannote/speaker-diarization-3.1"
                )
            DIAR_PIPELINE = load_diarization_pipeline(hf_token)
        return DIAR_PIPELINE


def _update(job: Job, *, stage: str, progress: float, message: str = "") -> None:
    with JOBS_LOCK:
        job.stage = stage
        job.progress = progress
        job.message = message
        job.status = "running"


def _run_job(
    job_id: str,
    audio_path: str,
    model_size: str,
    num_speakers: Optional[int],
    min_speakers: Optional[int],
    max_speakers: Optional[int],
    base_name: str,
) -> None:
    job = JOBS[job_id]
    try:
        _update(job, stage="converting", progress=0.05, message="Preparing audio...")
        wav_path = load_audio(audio_path, output_dir=AUDIO_DIR)

        _update(job, stage="diarizing", progress=0.2, message="Identifying speakers...")
        diar_pipeline = _get_diarization_pipeline()
        diar_segments = diarize(
            diar_pipeline,
            wav_path,
            num_speakers=num_speakers,
            min_speakers=min_speakers,
            max_speakers=max_speakers,
        )
        diar_segments = normalize_speaker_labels(diar_segments)

        _update(job, stage="transcribing", progress=0.55, message="Transcribing speech...")
        whisper_model = _get_whisper_model(model_size)
        transcription_segments = transcribe(whisper_model, wav_path)

        _update(job, stage="merging", progress=0.9, message="Merging segments...")
        merged = merge_consecutive(assign_speakers(transcription_segments, diar_segments))

        pdf_path = save_pdf(merged, output_dir=TRANSCRIPT_DIR, base_name=base_name)

        speakers = []
        seen = set()
        for entry in merged:
            if entry["speaker"] not in seen:
                seen.add(entry["speaker"])
                speakers.append(entry["speaker"])

        with JOBS_LOCK:
            job.transcript = merged
            job.speakers = speakers
            job.pdf_path = pdf_path
            job.stage = "done"
            job.progress = 1.0
            job.message = f"Found {len(speakers)} speaker(s)."
            job.status = "done"
    except Exception as exc:
        with JOBS_LOCK:
            job.status = "error"
            job.stage = "error"
            job.error = str(exc)
            job.message = str(exc)
    finally:
        try:
            if os.path.exists(audio_path):
                os.remove(audio_path)
        except OSError:
            pass


app = FastAPI(title="Whisper + Diarization API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict:
    return {
        "status": "ok",
        "hf_token_configured": bool(os.getenv("HF_TOKEN")),
        "models": sorted(MODEL_CHOICES),
    }


@app.post("/api/jobs")
async def create_job(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    model: str = Form("base"),
    name: str = Form("transcript"),
    speakers: Optional[int] = Form(None),
    min_speakers: Optional[int] = Form(None),
    max_speakers: Optional[int] = Form(None),
) -> dict:
    if model not in MODEL_CHOICES:
        raise HTTPException(400, f"Invalid model. Choose from {sorted(MODEL_CHOICES)}.")
    if not file.filename:
        raise HTTPException(400, "Missing filename.")

    safe_name = "".join(c for c in name if c.isalnum() or c in ("-", "_")).strip() or "transcript"

    job_id = uuid.uuid4().hex
    ext = os.path.splitext(file.filename)[1] or ".wav"
    upload_path = os.path.join(UPLOAD_DIR, f"{job_id}{ext}")
    with open(upload_path, "wb") as dest:
        shutil.copyfileobj(file.file, dest)

    job = Job(id=job_id, base_name=safe_name)
    with JOBS_LOCK:
        JOBS[job_id] = job

    background_tasks.add_task(
        _run_job,
        job_id,
        upload_path,
        model,
        speakers,
        min_speakers,
        max_speakers,
        safe_name,
    )
    return {"job_id": job_id}


@app.get("/api/jobs/{job_id}")
def get_job(job_id: str) -> dict:
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(404, "Job not found.")
    with JOBS_LOCK:
        return {
            "id": job.id,
            "status": job.status,
            "stage": job.stage,
            "progress": job.progress,
            "message": job.message,
            "error": job.error,
            "transcript": job.transcript,
            "speakers": job.speakers,
            "base_name": job.base_name,
            "has_pdf": bool(job.pdf_path and os.path.exists(job.pdf_path)),
        }


@app.get("/api/jobs/{job_id}/pdf")
def download_pdf(job_id: str):
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(404, "Job not found.")
    if not job.pdf_path or not os.path.exists(job.pdf_path):
        raise HTTPException(404, "PDF not ready.")
    return FileResponse(
        job.pdf_path,
        media_type="application/pdf",
        filename=f"{job.base_name}.pdf",
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=False)
