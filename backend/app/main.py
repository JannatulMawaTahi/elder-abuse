"""
Elder Abuse AI — FastAPI Backend

Guided Bangla yes/no assessment + TTS + legal analysis + admin dashboard.

The question flow is STATELESS: the frontend holds the `answers` dict and sends
it with every call. No server-side sessions — so a server restart or a second
worker never loses a user mid-flow, and deployment stays trivial.

    ── Guided flow (elder app) ──────────────────────────────────
    POST /flow/next          answers → next screen + progress bar
    GET  /flow/categories    6 category buttons (murder only for 3rd-party)
    GET  /flow/divisions     8 divisions
    GET  /flow/districts     districts of one division
    POST /analyze            answers → abuse type + risk + law + explanation
    GET  /tts                Bangla text → spoken audio (mp3, cached)
    POST /save-report        save ONLY if consent=true (anonymized)

    ── Optional free voice ("আরও কিছু বলতে চান?") ───────────────
    POST /transcribe         audio → text + classification
    POST /transcribe/text    text  → classification (debug)

    ── Admin dashboard (password-protected) ─────────────────────
    POST /dashboard/login    password → ok
    GET  /dashboard/stats    live Firestore analytics (6 charts)

Run:
    cd backend
    uvicorn app.main:app --reload --port 8000
    → http://localhost:8000/docs
"""

import os
import shutil
import tempfile
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, File, Header, HTTPException, Query, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field

from . import storage, tts_service
from .keyword_classifier import KeywordClassifier
from .preprocessor import (
    AudioPreprocessError,
    AudioTooLongError,
    AudioTooShortError,
    preprocess_audio,
)
from .question_engine import QuestionEngine, get_engine as get_question_engine
from .rag_engine import GeminiKeyMissingError, RagEngineError, get_engine as get_rag_engine
from .whisper_service import (
    WhisperAPIError,
    WhisperAPIKeyMissingError,
    transcribe,
)

load_dotenv()

# ── Constants ─────────────────────────────────────────────────────────────────
APP_VERSION = "0.2.0"
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")

ALLOWED_AUDIO_TYPES = {
    "audio/wav", "audio/x-wav", "audio/wave",
    "audio/mpeg", "audio/mp3",
    "audio/webm", "audio/ogg",
    "audio/mp4", "audio/x-m4a", "audio/m4a",
    "audio/flac", "audio/x-flac",
    "application/octet-stream",  # browsers sometimes send this
}
ALLOWED_AUDIO_EXTENSIONS = {".wav", ".mp3", ".webm", ".ogg", ".m4a", ".flac", ".mp4"}


# ── Lifespan: load engines once at startup ────────────────────────────────────
classifier: KeywordClassifier | None = None
questions:  QuestionEngine | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global classifier, questions
    print("[startup] Loading keyword classifier...")
    classifier = KeywordClassifier()
    print(f"[startup] Classifier loaded — {len(classifier.keywords)} categories")

    print("[startup] Loading question engine...")
    questions = get_question_engine()
    print(f"[startup] Question bank loaded — {len(questions.categories)} categories, "
          f"{len(questions.divisions)} divisions")

    print(f"[startup] Storage backend: {storage.backend_name()}")
    yield
    print("[shutdown] Server stopping")


app = FastAPI(
    title="Elder Abuse AI — Backend API",
    version=APP_VERSION,
    description=(
        "Guided Bangla voice assessment for elder abuse detection & legal "
        "assistance (Bangladesh), plus an admin dashboard for researchers."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Models ────────────────────────────────────────────────────────────────────
class HealthResponse(BaseModel):
    status:  str = "ok"
    version: str = APP_VERSION
    service: str = "elder-abuse-ai-backend"
    storage: str = ""


class AnswersRequest(BaseModel):
    """The whole answer dict collected so far. Client-held, stateless."""
    answers: dict[str, Any] = Field(default_factory=dict)


class NextScreenResponse(BaseModel):
    done:     bool                        # true → flow complete, call /analyze
    screen:   dict[str, Any] | None = None
    progress: dict[str, Any] = Field(default_factory=dict)


class SaveReportRequest(BaseModel):
    answers: dict[str, Any]
    consent: bool = False


class SaveReportResponse(BaseModel):
    saved:   bool
    id:      str | None = None
    backend: str | None = None
    message: str = ""


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


# ── Admin auth ────────────────────────────────────────────────────────────────
def require_admin(x_admin_password: str = Header(default="")) -> None:
    """Guards the dashboard. Password lives in .env (ADMIN_PASSWORD)."""
    if not ADMIN_PASSWORD:
        raise HTTPException(500, "ADMIN_PASSWORD is not configured on the server.")
    if x_admin_password != ADMIN_PASSWORD:
        raise HTTPException(401, "ভুল পাসওয়ার্ড")


# ── Meta ──────────────────────────────────────────────────────────────────────
@app.get("/health", response_model=HealthResponse, tags=["meta"])
def health_check():
    return HealthResponse(storage=storage.backend_name())


@app.get("/", include_in_schema=False)
def root():
    return JSONResponse({
        "service": "Elder Abuse AI Backend",
        "version": APP_VERSION,
        "docs":    "/docs",
        "health":  "/health",
    })


# ══════════════════════════════════════════════════════════════════════════════
#  GUIDED Q&A FLOW
# ══════════════════════════════════════════════════════════════════════════════
@app.post("/flow/next", response_model=NextScreenResponse, tags=["flow"])
def flow_next(req: AnswersRequest):
    """
    Given everything answered so far, return the next screen to show.

    `done: true` means the questions are over — the client should call /analyze.
    Branch logic (skipped categories, show_if, third-party-only) is applied here,
    so the frontend never has to know the rules.
    """
    screen = questions.next_screen(req.answers)
    return NextScreenResponse(
        done     = screen is None,
        screen   = screen,
        progress = questions.progress(req.answers),
    )


@app.get("/flow/categories", tags=["flow"])
def flow_categories(reporter_type: str | None = Query(default=None)):
    """Category buttons. 'মৃত্যুর ঘটনা' appears only for third-party reports."""
    return {"options": questions.category_options(reporter_type)}


@app.get("/flow/divisions", tags=["flow"])
def flow_divisions():
    return {"divisions": list(questions.divisions.keys())}


@app.get("/flow/districts", tags=["flow"])
def flow_districts(division: str = Query(..., description="e.g. ঢাকা")):
    districts = questions.districts_for(division)
    if not districts:
        raise HTTPException(404, f"বিভাগ পাওয়া যায়নি: {division}")
    return {"division": division, "districts": districts}


# ══════════════════════════════════════════════════════════════════════════════
#  ANALYSIS  — answers → abuse type + risk + violated law + explanation
# ══════════════════════════════════════════════════════════════════════════════
@app.post("/analyze", tags=["analyze"])
def analyze(req: AnswersRequest):
    """
    The result screen's data.

    Rule engine (deterministic) decides abuse type / severity / risk / confidence
    — these are the numbers the thesis measures. Gemini then adds the Bangla
    explanation, possible causes and next steps on top of that decision; it does
    not override it.
    """
    start = time.time()
    answers = req.answers

    assessment = questions.assess(answers)
    summary_bn = questions.build_summary(answers)

    try:
        result = get_rag_engine().analyze_assessment(summary_bn, assessment)
    except GeminiKeyMissingError as e:
        raise HTTPException(500, f"Server config error: {e}") from e
    except RagEngineError as e:
        # Gemini down → still return the deterministic result, minus the prose.
        result = {
            **assessment,
            "explanation_bn":     "",
            "possible_causes_bn": [],
            "recommendations_bn": assessment.get("recommendations_bn", []),
            "disclaimer_bn":      "এই ফলাফলটি আপনার দেওয়া উত্তরের ভিত্তিতে তৈরি। "
                                  "এটি চূড়ান্ত আইনি সিদ্ধান্ত নয়।",
            "degraded":           True,
            "degraded_reason":    str(e),
        }

    result["summary_bn"] = summary_bn
    result["processing_time_sec"] = round(time.time() - start, 2)
    return result


# ══════════════════════════════════════════════════════════════════════════════
#  TTS  — every Bangla question / result is read aloud
# ══════════════════════════════════════════════════════════════════════════════
@app.get("/tts", tags=["tts"], response_class=Response)
async def tts(
    text:  str = Query(..., min_length=1, max_length=1000),
    voice: str | None = Query(default=None, description="female (default) | male"),
):
    """Bangla text → mp3. Cached on disk, so repeat questions return in ~30 ms."""
    try:
        audio = await tts_service.synthesize(text, voice=voice)
    except tts_service.TTSError as e:
        raise HTTPException(502, f"TTS failed: {e}") from e

    return Response(
        content=audio,
        media_type="audio/mpeg",
        headers={"Cache-Control": "public, max-age=86400"},
    )


# ══════════════════════════════════════════════════════════════════════════════
#  SAVE  — anonymized, and ONLY with consent
# ══════════════════════════════════════════════════════════════════════════════
@app.post("/save-report", response_model=SaveReportResponse, tags=["save"])
def save_report(req: SaveReportRequest):
    """
    Saves an anonymized record for the dashboard — only if the user said হ্যাঁ.

    The record is rebuilt on the server from the answers (never trusted from the
    client), then passed through storage.sanitize(), which whitelists 10 analytics
    fields. No name, phone, address or free-text can reach the database.
    """
    if not req.consent:
        return SaveReportResponse(
            saved=False,
            message="সম্মতি দেননি — কিছুই সংরক্ষণ করা হয়নি।",
        )

    assessment = questions.assess(req.answers)
    record = questions.dashboard_record(req.answers, assessment)

    try:
        res = storage.save_assessment(record, consent=True)
    except storage.StorageError as e:
        raise HTTPException(502, f"সংরক্ষণ ব্যর্থ: {e}") from e

    return SaveReportResponse(
        saved=True, id=res["id"], backend=res["backend"],
        message="ধন্যবাদ। আপনার তথ্য নাম-পরিচয় ছাড়া সংরক্ষণ করা হয়েছে।",
    )


# ══════════════════════════════════════════════════════════════════════════════
#  ADMIN DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
class LoginRequest(BaseModel):
    password: str


@app.post("/dashboard/login", tags=["dashboard"])
def dashboard_login(req: LoginRequest):
    if not ADMIN_PASSWORD:
        raise HTTPException(500, "ADMIN_PASSWORD is not configured on the server.")
    if req.password != ADMIN_PASSWORD:
        raise HTTPException(401, "ভুল পাসওয়ার্ড")
    return {"ok": True}


@app.get("/dashboard/stats", tags=["dashboard"], dependencies=[Depends(require_admin)])
def dashboard_stats():
    """Live analytics from the saved (consented, anonymized) reports."""
    try:
        return storage.dashboard_stats()
    except storage.StorageError as e:
        raise HTTPException(502, f"Dashboard read failed: {e}") from e


# ══════════════════════════════════════════════════════════════════════════════
#  OPTIONAL FREE VOICE  — "আরও কিছু বলতে চান?"
# ══════════════════════════════════════════════════════════════════════════════
def _validate_audio_file(file: UploadFile) -> None:
    ext = Path(file.filename or "").suffix.lower()
    content_type = (file.content_type or "").lower()
    if ext not in ALLOWED_AUDIO_EXTENSIONS and content_type not in ALLOWED_AUDIO_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported audio format. Allowed: {sorted(ALLOWED_AUDIO_EXTENSIONS)}",
        )


@app.post("/transcribe", response_model=TranscribeResponse, tags=["voice"])
async def transcribe_audio(
    audio: UploadFile = File(..., description="Audio file (wav, mp3, webm, m4a, ogg, flac)")
):
    """Audio → preprocess → Whisper → keyword classify."""
    start_time = time.time()
    _validate_audio_file(audio)

    suffix = Path(audio.filename or "input.audio").suffix.lower() or ".audio"
    tmp_in = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
    tmp_wav_path: str | None = None
    try:
        try:
            shutil.copyfileobj(audio.file, tmp_in)
        finally:
            tmp_in.close()

        try:
            pp_result = preprocess_audio(tmp_in.name)
            tmp_wav_path = pp_result["wav_path"]
        except AudioTooShortError as e:
            raise HTTPException(400, f"Audio too short: {e}") from e
        except AudioTooLongError as e:
            raise HTTPException(400, f"Audio too long: {e}") from e
        except AudioPreprocessError as e:
            raise HTTPException(400, f"Audio preprocessing failed: {e}") from e

        try:
            w_result = transcribe(tmp_wav_path)
        except WhisperAPIKeyMissingError as e:
            raise HTTPException(500, f"Server config error: {e}") from e
        except WhisperAPIError as e:
            raise HTTPException(502, f"Whisper API error: {e}") from e

        c_result = classifier.classify(w_result["text"])

        return TranscribeResponse(
            transcript=TranscriptResult(
                text          = w_result["text"],
                language_mode = w_result["language_mode"],
                detected_lang = w_result["detected_lang"],
                duration_sec  = w_result["duration_sec"],
            ),
            classification=ClassificationResult(**{
                k: c_result[k] for k in ClassificationResult.model_fields
            }),
            entities=EntitiesResult(**c_result["entities"]),
            processing_time_sec=round(time.time() - start_time, 2),
        )
    finally:
        for path in (tmp_in.name, tmp_wav_path):
            if path and os.path.exists(path):
                try:
                    os.unlink(path)
                except OSError:
                    pass


@app.post("/transcribe/text", response_model=TranscribeResponse, tags=["voice"])
def transcribe_text(request: TextRequest):
    """Direct text → classification (skips audio + Whisper). For testing."""
    start_time = time.time()
    c_result = classifier.classify(request.text)

    return TranscribeResponse(
        transcript=None,
        classification=ClassificationResult(**{
            k: c_result[k] for k in ClassificationResult.model_fields
        }),
        entities=EntitiesResult(**c_result["entities"]),
        processing_time_sec=round(time.time() - start_time, 4),
    )
