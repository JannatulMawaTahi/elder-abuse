"""
TTS Service — Bangla text → speech (edge-tts, Bangladeshi neural voices).

Why this exists: many elderly users cannot read. The app SPEAKS every question
and the result aloud (🔊 শুনুন on every screen), so the elder can participate
(hear, answer, understand) even without literacy.

Voices (free, no API key):
    bn-BD-NabanitaNeural  — Female (default; warm, clear)
    bn-BD-PradeepNeural   — Male

Audio is cached on disk keyed by (text, voice, rate) — the same question is
only ever synthesised once, so the flow feels instant after first use.
"""

import asyncio
import hashlib
from pathlib import Path

import edge_tts

CACHE_DIR = Path(__file__).parent.parent / "tts_cache"

VOICE_FEMALE = "bn-BD-NabanitaNeural"
VOICE_MALE   = "bn-BD-PradeepNeural"
DEFAULT_VOICE = VOICE_FEMALE

# Normal speed — slowing it down made the voice sound broken/unnatural (tested).
DEFAULT_RATE = "+0%"

VOICES = {"female": VOICE_FEMALE, "male": VOICE_MALE}


class TTSError(Exception):
    pass


def _cache_path(text: str, voice: str, rate: str) -> Path:
    key = hashlib.sha256(f"{voice}|{rate}|{text}".encode("utf-8")).hexdigest()[:32]
    return CACHE_DIR / f"{key}.mp3"


def resolve_voice(voice: str | None) -> str:
    """Accept 'female' / 'male' / a full bn-BD-* name."""
    if not voice:
        return DEFAULT_VOICE
    if voice in VOICES:
        return VOICES[voice]
    if voice.startswith("bn-"):
        return voice
    return DEFAULT_VOICE


async def synthesize(text: str,
                     voice: str | None = None,
                     rate: str = DEFAULT_RATE,
                     use_cache: bool = True) -> bytes:
    """
    Bangla text → MP3 bytes.

    Raises TTSError on empty text or synthesis failure.
    """
    text = (text or "").strip()
    if not text:
        raise TTSError("Empty text — nothing to speak")

    v = resolve_voice(voice)
    cache_file = _cache_path(text, v, rate)

    if use_cache and cache_file.exists():
        return cache_file.read_bytes()

    try:
        communicate = edge_tts.Communicate(text, v, rate=rate)
        audio = bytearray()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio.extend(chunk["data"])
    except Exception as e:
        raise TTSError(f"TTS synthesis failed: {e}") from e

    if not audio:
        raise TTSError("TTS returned no audio")

    if use_cache:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        cache_file.write_bytes(bytes(audio))

    return bytes(audio)


def synthesize_sync(text: str,
                    voice: str | None = None,
                    rate: str = DEFAULT_RATE,
                    use_cache: bool = True) -> bytes:
    """Blocking wrapper (scripts / tests). FastAPI should await synthesize()."""
    return asyncio.run(synthesize(text, voice, rate, use_cache))


async def prewarm(texts: list[str], voice: str | None = None) -> int:
    """
    Pre-generate audio for a list of texts (e.g. every question in the bank)
    so the first user never waits. Returns how many were newly synthesised.
    """
    made = 0
    for t in texts:
        t = (t or "").strip()
        if not t:
            continue
        v = resolve_voice(voice)
        if _cache_path(t, v, DEFAULT_RATE).exists():
            continue
        await synthesize(t, voice)
        made += 1
    return made


def cache_stats() -> dict[str, int | float]:
    if not CACHE_DIR.exists():
        return {"files": 0, "size_kb": 0.0}
    files = list(CACHE_DIR.glob("*.mp3"))
    return {
        "files":   len(files),
        "size_kb": round(sum(f.stat().st_size for f in files) / 1024, 1),
    }


# ── CLI ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")

    text = " ".join(sys.argv[1:]) or (
        "স্বাগতম। আমি আপনার সমস্যাটি বুঝতে কিছু সহজ প্রশ্ন করব। "
        "সব তথ্য গোপন রাখা হবে।"
    )
    print(f"Text : {text}")
    print(f"Voice: {DEFAULT_VOICE}  (rate {DEFAULT_RATE})")

    audio = synthesize_sync(text)
    out = Path("tts_sample.mp3")
    out.write_bytes(audio)
    print(f"Saved: {out.resolve()}  ({len(audio)/1024:.1f} KB)")
    print(f"Cache: {cache_stats()}")
