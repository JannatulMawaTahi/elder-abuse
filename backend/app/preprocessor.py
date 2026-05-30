"""
Audio Preprocessor — যেকোনো audio file → Whisper-ready WAV format

Input  : webm, mp3, m4a, ogg, flac, wav (যেকোনো ffmpeg-supported format)
Output : 16kHz mono WAV, normalized to -3.0 dBFS

Used by /transcribe endpoint before sending to Whisper API.
"""

import os
from pathlib import Path
from pydub import AudioSegment


# ── Constants ─────────────────────────────────────────────────────────────────
TARGET_SAMPLE_RATE = 16000      # Whisper এর native rate
TARGET_CHANNELS    = 1          # mono
TARGET_DBFS        = -3.0       # peak normalize level
MIN_DURATION_SEC   = 0.5        # too short audio reject
MAX_DURATION_SEC   = 300        # > 5 min reject (Groq API limit ~25 MB)


# ── Custom Exceptions ─────────────────────────────────────────────────────────
class AudioPreprocessError(Exception):
    """Audio preprocessing failed."""


class AudioTooShortError(AudioPreprocessError):
    """Audio is shorter than minimum required duration."""


class AudioTooLongError(AudioPreprocessError):
    """Audio exceeds maximum allowed duration."""


# ── Main Function ─────────────────────────────────────────────────────────────
def preprocess_audio(input_path: str, output_path: str | None = None) -> dict:
    """
    Convert any audio file → 16kHz mono WAV, normalized.

    Args:
        input_path  : Source audio file path (any format)
        output_path : Optional output path. If None, auto-generated.

    Returns:
        {
            "wav_path":            "/path/to/output.wav",
            "duration_sec":        12.4,
            "original_sample_rate": 48000,
            "original_channels":    2,
            "original_format":      ".webm",
            "size_kb":              198.3
        }

    Raises:
        FileNotFoundError      : If input file does not exist
        AudioTooShortError     : If audio < 0.5 seconds
        AudioTooLongError      : If audio > 300 seconds
        AudioPreprocessError   : Any other processing error
    """
    in_path = Path(input_path)

    if not in_path.exists():
        raise FileNotFoundError(f"Input audio file not found: {input_path}")

    # Auto-generate output path if not given
    if output_path is None:
        output_path = str(in_path.with_suffix('.processed.wav'))

    try:
        # Load audio (ffmpeg detects format automatically)
        audio = AudioSegment.from_file(input_path)
    except Exception as e:
        raise AudioPreprocessError(f"Failed to load audio: {e}") from e

    original_sr       = audio.frame_rate
    original_channels = audio.channels
    duration_sec      = len(audio) / 1000.0

    # Duration checks
    if duration_sec < MIN_DURATION_SEC:
        raise AudioTooShortError(
            f"Audio duration {duration_sec:.2f}s is below minimum {MIN_DURATION_SEC}s"
        )
    if duration_sec > MAX_DURATION_SEC:
        raise AudioTooLongError(
            f"Audio duration {duration_sec:.2f}s exceeds maximum {MAX_DURATION_SEC}s"
        )

    # ── Step 1: Convert channels → mono ──────────────────────────────────────
    if audio.channels > 1:
        audio = audio.set_channels(TARGET_CHANNELS)

    # ── Step 2: Convert sample rate → 16000 Hz ───────────────────────────────
    if audio.frame_rate != TARGET_SAMPLE_RATE:
        audio = audio.set_frame_rate(TARGET_SAMPLE_RATE)

    # ── Step 3: Normalize volume → -3.0 dBFS peak ────────────────────────────
    gain_db = TARGET_DBFS - audio.max_dBFS
    if abs(gain_db) > 0.1:
        audio = audio.apply_gain(gain_db)

    # ── Step 4: Export as WAV (PCM 16-bit) ───────────────────────────────────
    try:
        audio.export(
            output_path,
            format='wav',
            parameters=['-acodec', 'pcm_s16le']
        )
    except Exception as e:
        raise AudioPreprocessError(f"Failed to export WAV: {e}") from e

    size_kb = os.path.getsize(output_path) / 1024

    return {
        "wav_path":             output_path,
        "duration_sec":         round(duration_sec, 2),
        "original_sample_rate": original_sr,
        "original_channels":    original_channels,
        "original_format":      in_path.suffix.lower(),
        "size_kb":              round(size_kb, 2),
    }


# ── CLI for quick manual test ─────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python preprocessor.py <input_audio_file>")
        sys.exit(1)

    result = preprocess_audio(sys.argv[1])
    print("Preprocessing successful:")
    for k, v in result.items():
        print(f"  {k:<22}: {v}")
