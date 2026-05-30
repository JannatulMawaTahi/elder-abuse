"""
Whisper Service — Speech-to-Text via Groq Whisper API

Sends preprocessed WAV → Groq Whisper Large-v3-Turbo → text + language detection

Free tier: 28,800 audio seconds/day
API docs : https://console.groq.com/docs/speech-text

Used by /transcribe endpoint after preprocessor.py.
"""

import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from groq import Groq, APIError, APIConnectionError

# Load environment variables from .env
load_dotenv(Path(__file__).parent.parent / ".env")


# ── Constants ─────────────────────────────────────────────────────────────────
WHISPER_MODEL    = "whisper-large-v3-turbo"
DEFAULT_PROMPT   = (
    "This is a complaint about elder abuse in Bangladesh. "
    "Speaker may use Bangla, English, or a mix of both languages. "
    "Common terms: UNO, PMA, NLASO, পিতামাতা, ভরণপোষণ, নির্যাতন."
)


# ── Custom Exceptions ─────────────────────────────────────────────────────────
class WhisperServiceError(Exception):
    """Base error for whisper service."""


class WhisperAPIKeyMissingError(WhisperServiceError):
    """GROQ_API_KEY not set in environment."""


class WhisperAPIError(WhisperServiceError):
    """API call failed (network, rate limit, server error)."""


# ── Client Setup (lazy) ───────────────────────────────────────────────────────
_client: Groq | None = None


def _get_client() -> Groq:
    """Lazy-init Groq client. Raises if API key missing."""
    global _client
    if _client is None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key or api_key.startswith("gsk_your_"):
            raise WhisperAPIKeyMissingError(
                "GROQ_API_KEY not set. Add it to backend/.env file."
            )
        _client = Groq(api_key=api_key)
    return _client


# ── Language Detection Helper ─────────────────────────────────────────────────
def detect_language_mode(text: str) -> str:
    """
    Detect language mode from script characters present.

    Returns: 'bangla' | 'english' | 'mixed' | 'unknown'
    """
    if not text or not text.strip():
        return "unknown"

    has_bangla  = any('ঀ' <= ch <= '৿' for ch in text)
    has_english = any(ch.isascii() and ch.isalpha() for ch in text)

    if has_bangla and has_english:
        # Count words to decide majority
        bn_chars = sum(1 for ch in text if 'ঀ' <= ch <= '৿')
        en_chars = sum(1 for ch in text if ch.isascii() and ch.isalpha())
        # If one script is >80% of letter content, classify as that
        total = bn_chars + en_chars
        if bn_chars / total > 0.8:
            return "bangla"
        if en_chars / total > 0.8:
            return "english"
        return "mixed"
    if has_bangla:
        return "bangla"
    if has_english:
        return "english"
    return "unknown"


# ── Main Function ─────────────────────────────────────────────────────────────
def transcribe(wav_path: str, prompt: str | None = None) -> dict[str, Any]:
    """
    Transcribe WAV audio using Groq Whisper API.

    Args:
        wav_path : Path to 16kHz mono WAV file (use preprocessor.py first)
        prompt   : Optional context hint to improve accuracy

    Returns:
        {
            "text":           "আমার ছেলে মারধর করেছে",
            "language_mode":  "bangla",      # bangla | english | mixed
            "detected_lang":  "bn",          # Whisper's ISO code
            "duration_sec":   12.4,
            "segments":       [...],         # list of {start, end, text}
            "model":          "whisper-large-v3-turbo"
        }

    Raises:
        FileNotFoundError          : WAV file not found
        WhisperAPIKeyMissingError  : GROQ_API_KEY missing in .env
        WhisperAPIError            : API call failed
    """
    if not os.path.exists(wav_path):
        raise FileNotFoundError(f"WAV file not found: {wav_path}")

    client = _get_client()
    use_prompt = prompt if prompt is not None else DEFAULT_PROMPT

    try:
        with open(wav_path, "rb") as f:
            response = client.audio.transcriptions.create(
                file=(os.path.basename(wav_path), f.read()),
                model=WHISPER_MODEL,
                response_format="verbose_json",
                prompt=use_prompt,
                # NO language= parameter → auto-detect
            )
    except APIConnectionError as e:
        raise WhisperAPIError(f"Network error calling Groq API: {e}") from e
    except APIError as e:
        raise WhisperAPIError(f"Groq API returned error: {e}") from e
    except Exception as e:
        raise WhisperAPIError(f"Unexpected error: {e}") from e

    # Extract fields from response object
    text          = getattr(response, "text", "") or ""
    detected_lang = getattr(response, "language", "unknown") or "unknown"
    duration      = getattr(response, "duration", 0.0) or 0.0
    segments_raw  = getattr(response, "segments", []) or []

    # Normalize segments to simple dicts
    segments = []
    for seg in segments_raw:
        if isinstance(seg, dict):
            segments.append({
                "start": seg.get("start", 0.0),
                "end":   seg.get("end",   0.0),
                "text":  seg.get("text", ""),
            })
        else:
            segments.append({
                "start": getattr(seg, "start", 0.0),
                "end":   getattr(seg, "end",   0.0),
                "text":  getattr(seg, "text", ""),
            })

    return {
        "text":          text.strip(),
        "language_mode": detect_language_mode(text),
        "detected_lang": detected_lang,
        "duration_sec":  round(duration, 2),
        "segments":      segments,
        "model":         WHISPER_MODEL,
    }


# ── CLI for quick manual test ─────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python whisper_service.py <wav_file>")
        sys.exit(1)

    result = transcribe(sys.argv[1])
    print("\nTranscription result:")
    print(f"  Text         : {result['text']}")
    print(f"  Language mode: {result['language_mode']}")
    print(f"  Detected lang: {result['detected_lang']}")
    print(f"  Duration     : {result['duration_sec']}s")
    print(f"  Segments     : {len(result['segments'])}")
