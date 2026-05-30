"""
Elder Abuse AI — FastAPI Backend

Endpoints:
    GET  /health              → Health check
    POST /transcribe          → Audio file → text + classification
    POST /transcribe/text     → Direct text → classification (debug/test)
    GET  /docs                → Auto-generated Swagger UI

Run:
    cd backend
    uvicorn app.main:app --reload --port 8000

Then open: http://localhost:8000/docs
"""

import os
import shutil
import tempfile
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from .keyword_classifier import KeywordClassifier
from .preprocessor import (
    AudioPreprocessError,
    AudioTooLongError,
    AudioTooShortError,
    preprocess_audio,
)
from .whisper_service import (
    WhisperAPIError,
    WhisperAPIKeyMissingError,
    transcribe,
)


# ── Constants ─────────────────────────────────────────────────────────────────
APP_VERSION   = "0.1.0"
ALLOWED_AUDIO_TYPES = {
    "audio/wav", "audio/x-wav", "audio/wave",
    "audio/mpeg", "audio/mp3",
    "audio/webm", "audio/ogg",
    "audio/mp4", "audio/x-m4a", "audio/m4a",
    "audio/flac", "audio/x-flac",
    "application/octet-stream",  # browsers sometimes send this
}
ALLOWED_AUDIO_EXTENSIONS = {".wav", ".mp3", ".webm", ".ogg", ".m4a", ".flac", ".mp4"}


# ── Lifespan: load classifier once at startup ─────────────────────────────────
classifier: KeywordClassifier | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize shared resources at server startup."""
    global classifier
    print("[startup] Loading keyword classifier...")
    classifier = KeywordClassifier()
    print(f"[startup] Classifier loaded with {len(classifier.keywords)} categories")
    yield
    print("[shutdown] Server stopping")


# ── App setup ─────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Elder Abuse AI — Backend API",
    version=APP_VERSION,
    description=(
        "Voice-first AI system for elder abuse detection & legal assistance "
        "(Bangladesh). Phase 2 — Speech-to-text + Classification."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",  # CRA dev server
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Pydantic Models ───────────────────────────────────────────────────────────
class HealthResponse(BaseModel):
    status:  str = "ok"
    version: str = APP_VERSION
    service: str = "elder-abuse-ai-backend"


class TextRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000,
                      description="Complaint text in Bangla, English, or Mixed")


class ClassificationResult(BaseModel):
    category:            str
    all_categories:      dict[str, int]
    severity:            int
    confidence:          float
    matched_keywords:    list[str]
    legal_sections:      list[str]
    civil_or_criminal:   str
    recommended_action:  str


class EntitiesResult(BaseModel):
    age:              int | None = None
    victim_relation:  str | None = None
    abuser_relation:  str | None = None


class TranscriptResult(BaseModel):
    text:           str
    language_mode:  str
    detected_lang:  str
    duration_sec:   float


class TranscribeResponse(BaseModel):
    success:             bool = True
    transcript:          TranscriptResult | None = None
    classification:      ClassificationResult
    entities:            EntitiesResult
    processing_time_sec: float


# ── Helper: validate audio upload ─────────────────────────────────────────────
def _validate_audio_file(file: UploadFile) -> None:
    """Reject non-audio files."""
    ext = Path(file.filename or "").suffix.lower()
    content_type = (file.content_type or "").lower()

    if ext not in ALLOWED_AUDIO_EXTENSIONS and content_type not in ALLOWED_AUDIO_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=(
                f"Unsupported audio format. "
                f"Allowed extensions: {sorted(ALLOWED_AUDIO_EXTENSIONS)}"
            ),
        )


# ── Endpoint: /health ─────────────────────────────────────────────────────────
@app.get("/health", response_model=HealthResponse, tags=["meta"])
def health_check():
    """Simple health check — returns 200 if server is running."""
    return HealthResponse()


# ── Endpoint: /transcribe (audio) ─────────────────────────────────────────────
@app.post("/transcribe", response_model=TranscribeResponse, tags=["transcribe"])
async def transcribe_audio(audio: UploadFile = File(..., description="Audio file (wav, mp3, webm, m4a, ogg, flac)")):
    """
    Full pipeline: Audio → preprocess → Whisper → keyword classify → response.
    """
    start_time = time.time()
    _validate_audio_file(audio)

    # 1. Save uploaded file to temp
    suffix = Path(audio.filename or "input.audio").suffix.lower() or ".audio"
    tmp_in = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
    tmp_wav_path: str | None = None
    try:
        try:
            shutil.copyfileobj(audio.file, tmp_in)
        finally:
            tmp_in.close()

        # 2. Preprocess → 16kHz mono WAV
        try:
            pp_result = preprocess_audio(tmp_in.name)
            tmp_wav_path = pp_result["wav_path"]
        except AudioTooShortError as e:
            raise HTTPException(status_code=400, detail=f"Audio too short: {e}") from e
        except AudioTooLongError as e:
            raise HTTPException(status_code=400, detail=f"Audio too long: {e}") from e
        except AudioPreprocessError as e:
            raise HTTPException(status_code=400, detail=f"Audio preprocessing failed: {e}") from e

        # 3. Transcribe via Groq Whisper
        try:
            w_result = transcribe(tmp_wav_path)
        except WhisperAPIKeyMissingError as e:
            raise HTTPException(status_code=500, detail=f"Server config error: {e}") from e
        except WhisperAPIError as e:
            raise HTTPException(status_code=502, detail=f"Whisper API error: {e}") from e

        # 4. Classify text
        c_result = classifier.classify(w_result["text"])

        # 5. Build response
        return TranscribeResponse(
            transcript=TranscriptResult(
                text          = w_result["text"],
                language_mode = w_result["language_mode"],
                detected_lang = w_result["detected_lang"],
                duration_sec  = w_result["duration_sec"],
            ),
            classification=ClassificationResult(
                category           = c_result["category"],
                all_categories     = c_result["all_categories"],
                severity           = c_result["severity"],
                confidence         = c_result["confidence"],
                matched_keywords   = c_result["matched_keywords"],
                legal_sections     = c_result["legal_sections"],
                civil_or_criminal  = c_result["civil_or_criminal"],
                recommended_action = c_result["recommended_action"],
            ),
            entities=EntitiesResult(**c_result["entities"]),
            processing_time_sec=round(time.time() - start_time, 2),
        )
    finally:
        # Cleanup temp files
        for path in (tmp_in.name, tmp_wav_path):
            if path and os.path.exists(path):
                try:
                    os.unlink(path)
                except OSError:
                    pass


# ── Endpoint: /transcribe/text (debug) ────────────────────────────────────────
@app.post("/transcribe/text", response_model=TranscribeResponse, tags=["transcribe"])
def transcribe_text(request: TextRequest):
    """
    Direct text input → classification (skips audio + Whisper).
    Useful for testing without recording audio.
    """
    start_time = time.time()
    c_result = classifier.classify(request.text)

    return TranscribeResponse(
        transcript=None,
        classification=ClassificationResult(
            category           = c_result["category"],
            all_categories     = c_result["all_categories"],
            severity           = c_result["severity"],
            confidence         = c_result["confidence"],
            matched_keywords   = c_result["matched_keywords"],
            legal_sections     = c_result["legal_sections"],
            civil_or_criminal  = c_result["civil_or_criminal"],
            recommended_action = c_result["recommended_action"],
        ),
        entities=EntitiesResult(**c_result["entities"]),
        processing_time_sec=round(time.time() - start_time, 4),
    )


# ── Root redirect to docs ─────────────────────────────────────────────────────
@app.get("/", include_in_schema=False)
def root():
    return JSONResponse({
        "service": "Elder Abuse AI Backend",
        "version": APP_VERSION,
        "docs":    "/docs",
        "health":  "/health",
    })
