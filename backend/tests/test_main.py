"""
Tests for backend/app/main.py (FastAPI server)

Run from backend/ folder:
    python -m pytest tests/test_main.py -v
"""

import io
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient
from pydub.generators import Sine

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import app


@pytest.fixture(scope="module")
def client():
    """Reusable TestClient that triggers app lifespan (classifier load)."""
    with TestClient(app) as c:
        yield c


def make_wav_bytes(duration_ms: int = 1500) -> bytes:
    """Generate a 16kHz mono WAV in-memory."""
    audio = Sine(440).to_audio_segment(duration=duration_ms)
    audio = audio.set_frame_rate(16000).set_channels(1)
    buf = io.BytesIO()
    audio.export(buf, format='wav')
    buf.seek(0)
    return buf.read()


# ════════════════════════════════════════════════════════════════════════════════
# /health
# ════════════════════════════════════════════════════════════════════════════════
class TestHealth:

    def test_health_returns_200(self, client):
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_response_structure(self, client):
        response = client.get("/health")
        data = response.json()
        assert data["status"]  == "ok"
        assert data["service"] == "elder-abuse-ai-backend"
        assert "version" in data


# ════════════════════════════════════════════════════════════════════════════════
# /transcribe/text
# ════════════════════════════════════════════════════════════════════════════════
class TestTranscribeText:

    def test_bangla_physical_abuse(self, client):
        response = client.post(
            "/transcribe/text",
            json={"text": "ছেলে আমাকে মারধর করেছে এবং আঘাত পেয়েছি"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"]                       is True
        assert data["transcript"]                    is None
        assert data["classification"]["category"]    == "physical"
        assert data["classification"]["severity"]    == 4

    def test_english_abandonment(self, client):
        response = client.post(
            "/transcribe/text",
            json={"text": "Mother was abandoned on the street by her children evicted"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["classification"]["category"] == "abandonment"

    def test_unknown_text(self, client):
        response = client.post(
            "/transcribe/text",
            json={"text": "আজকে আকাশ মেঘলা এবং বৃষ্টি হচ্ছে"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["classification"]["category"] == "unknown"
        assert data["classification"]["severity"] == 0

    def test_rejects_empty_text(self, client):
        response = client.post("/transcribe/text", json={"text": ""})
        assert response.status_code == 422  # Pydantic validation error

    def test_rejects_too_long_text(self, client):
        response = client.post("/transcribe/text", json={"text": "x" * 6000})
        assert response.status_code == 422

    def test_entities_extracted(self, client):
        response = client.post(
            "/transcribe/text",
            json={"text": "৭৫ বছরের বাবাকে ছেলে মারধর করেছে"}
        )
        data = response.json()
        assert data["entities"]["age"]              == 75
        assert data["entities"]["victim_relation"]  == "father"
        assert data["entities"]["abuser_relation"]  == "son"

    def test_processing_time_present(self, client):
        response = client.post(
            "/transcribe/text",
            json={"text": "ছেলে মারধর করেছে"}
        )
        assert "processing_time_sec" in response.json()


# ════════════════════════════════════════════════════════════════════════════════
# /transcribe (audio) — mocked Whisper to avoid real API calls in unit tests
# ════════════════════════════════════════════════════════════════════════════════
class TestTranscribeAudio:

    @patch("app.main.transcribe")
    def test_full_pipeline_with_mock_whisper(self, mock_transcribe, client):
        mock_transcribe.return_value = {
            "text":          "ছেলে আমাকে মারধর করেছে",
            "language_mode": "bangla",
            "detected_lang": "bn",
            "duration_sec":  1.5,
            "segments":      [],
            "model":         "whisper-large-v3-turbo",
        }
        wav_bytes = make_wav_bytes(1500)

        response = client.post(
            "/transcribe",
            files={"audio": ("test.wav", wav_bytes, "audio/wav")},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"]                          is True
        assert data["transcript"]["language_mode"]      == "bangla"
        assert data["classification"]["category"]       == "physical"
        assert data["processing_time_sec"]              > 0

    def test_rejects_non_audio_file(self, client):
        response = client.post(
            "/transcribe",
            files={"audio": ("test.txt", b"hello world", "text/plain")},
        )
        assert response.status_code == 415

    def test_rejects_too_short_audio(self, client):
        wav_bytes = make_wav_bytes(200)  # < 500ms minimum
        response = client.post(
            "/transcribe",
            files={"audio": ("short.wav", wav_bytes, "audio/wav")},
        )
        assert response.status_code == 400
        assert "too short" in response.json()["detail"].lower()

    def test_missing_audio_field(self, client):
        response = client.post("/transcribe")
        assert response.status_code == 422


# ════════════════════════════════════════════════════════════════════════════════
# CORS
# ════════════════════════════════════════════════════════════════════════════════
class TestCORS:

    def test_cors_headers_present_on_preflight(self, client):
        response = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert "access-control-allow-origin" in {k.lower() for k in response.headers}


# ════════════════════════════════════════════════════════════════════════════════
# Root
# ════════════════════════════════════════════════════════════════════════════════
class TestRoot:

    def test_root_returns_service_info(self, client):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert data["docs"]   == "/docs"
        assert data["health"] == "/health"
