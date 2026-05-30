"""
Tests for backend/app/whisper_service.py

Run from backend/ folder:
    python -m pytest tests/test_whisper_service.py -v

By default, the real API integration test is SKIPPED unless GROQ_API_KEY is set.
"""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from pydub.generators import Sine

# Make backend/app importable
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.whisper_service import (
    transcribe,
    detect_language_mode,
    WhisperAPIKeyMissingError,
    WhisperAPIError,
    WHISPER_MODEL,
)
from app.preprocessor import preprocess_audio


# ── Helpers ───────────────────────────────────────────────────────────────────
def make_test_wav(duration_ms: int = 1000, tmp_dir: str | None = None) -> str:
    """Create a 16kHz mono WAV with a tone (for real API test)."""
    audio = Sine(440).to_audio_segment(duration=duration_ms)
    audio = audio.set_frame_rate(16000).set_channels(1)

    fd, path = tempfile.mkstemp(suffix='.wav', dir=tmp_dir)
    os.close(fd)
    audio.export(path, format='wav')
    return path


def mock_whisper_response(text: str = "test", language: str = "en",
                          duration: float = 2.0):
    """Build a fake Whisper API response object."""
    response = MagicMock()
    response.text     = text
    response.language = language
    response.duration = duration
    response.segments = [
        {"start": 0.0, "end": duration, "text": text}
    ]
    return response


# ════════════════════════════════════════════════════════════════════════════════
# UNIT TESTS — Language detection logic (no API needed)
# ════════════════════════════════════════════════════════════════════════════════
class TestLanguageModeDetection:

    def test_pure_bangla(self):
        text = "আমার ছেলে মারধর করেছে"
        assert detect_language_mode(text) == "bangla"

    def test_pure_english(self):
        text = "My son has beaten me"
        assert detect_language_mode(text) == "english"

    def test_mixed_banglish(self):
        text = "আমার son আমাকে beat করেছে"
        assert detect_language_mode(text) == "mixed"

    def test_empty_text(self):
        assert detect_language_mode("") == "unknown"
        assert detect_language_mode("   ") == "unknown"

    def test_only_numbers_no_letters(self):
        assert detect_language_mode("12345 67890") == "unknown"

    def test_majority_bangla_with_few_english(self):
        """80%+ Bangla characters → classified as bangla"""
        text = "আমার ছেলে মারধর করেছে এবং বাড়ি থেকে evict করে দিয়েছে আমাকে"
        # Mostly Bangla, just one English word — should still be 'bangla'
        result = detect_language_mode(text)
        assert result in ("bangla", "mixed")  # Either acceptable

    def test_majority_english_with_few_bangla(self):
        """80%+ English → classified as english"""
        text = "He physically assaulted his elderly father and refused পরিচর্যা"
        result = detect_language_mode(text)
        assert result in ("english", "mixed")


# ════════════════════════════════════════════════════════════════════════════════
# UNIT TESTS — Transcribe function with mocked API
# ════════════════════════════════════════════════════════════════════════════════
class TestTranscribeWithMock:

    def test_raises_filenotfound_for_missing_wav(self):
        with pytest.raises(FileNotFoundError):
            transcribe('/nonexistent/path/audio.wav')

    @patch('app.whisper_service._get_client')
    def test_returns_expected_structure(self, mock_get_client, tmp_path):
        mock_client = MagicMock()
        mock_client.audio.transcriptions.create.return_value = \
            mock_whisper_response(text="Hello world", language="en", duration=2.0)
        mock_get_client.return_value = mock_client

        wav_path = make_test_wav(1000, tmp_dir=str(tmp_path))
        result   = transcribe(wav_path)

        assert result['text']          == "Hello world"
        assert result['language_mode'] == "english"
        assert result['detected_lang'] == "en"
        assert result['duration_sec']  == 2.0
        assert result['model']         == WHISPER_MODEL
        assert len(result['segments']) == 1

    @patch('app.whisper_service._get_client')
    def test_bangla_response(self, mock_get_client, tmp_path):
        mock_client = MagicMock()
        mock_client.audio.transcriptions.create.return_value = \
            mock_whisper_response(
                text="আমার ছেলে মারধর করেছে",
                language="bn",
                duration=3.5
            )
        mock_get_client.return_value = mock_client

        wav_path = make_test_wav(1000, tmp_dir=str(tmp_path))
        result   = transcribe(wav_path)

        assert result['language_mode'] == "bangla"
        assert "ছেলে" in result['text']

    @patch('app.whisper_service._get_client')
    def test_api_error_raises_whisper_api_error(self, mock_get_client, tmp_path):
        from groq import APIConnectionError
        mock_client = MagicMock()
        mock_client.audio.transcriptions.create.side_effect = \
            APIConnectionError(request=MagicMock())
        mock_get_client.return_value = mock_client

        wav_path = make_test_wav(1000, tmp_dir=str(tmp_path))
        with pytest.raises(WhisperAPIError):
            transcribe(wav_path)


# ════════════════════════════════════════════════════════════════════════════════
# INTEGRATION TEST — Real Groq API (skipped if no key)
# ════════════════════════════════════════════════════════════════════════════════
@pytest.mark.skipif(
    not os.getenv("GROQ_API_KEY") or os.getenv("GROQ_API_KEY", "").startswith("gsk_your_"),
    reason="GROQ_API_KEY not set in environment"
)
class TestRealGroqAPI:

    def test_real_api_call_with_silent_audio(self, tmp_path):
        """Verify real API call works end-to-end with a short audio sample."""
        # Reload .env in case test runs in fresh process
        from dotenv import load_dotenv
        load_dotenv(Path(__file__).parent.parent / ".env")
        # Reset module-level client to pick up env
        import app.whisper_service as ws
        ws._client = None

        wav_path = make_test_wav(1500, tmp_dir=str(tmp_path))
        result   = transcribe(wav_path)

        # Sine wave likely returns empty or non-meaningful text,
        # but the API call structure should work
        assert 'text'          in result
        assert 'language_mode' in result
        assert 'detected_lang' in result
        assert 'duration_sec'  in result
        assert result['model'] == WHISPER_MODEL
        print(f"\n  Real API response: text='{result['text'][:80]}', "
              f"lang={result['detected_lang']}, duration={result['duration_sec']}s")
