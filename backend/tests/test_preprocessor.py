"""
Tests for backend/app/preprocessor.py

Run from backend/ folder:
    python -m pytest tests/test_preprocessor.py -v
"""

import os
import sys
import tempfile
from pathlib import Path

import pytest
from pydub import AudioSegment
from pydub.generators import Sine

# Make backend/app importable when running pytest from backend/
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.preprocessor import (
    preprocess_audio,
    AudioPreprocessError,
    AudioTooShortError,
    AudioTooLongError,
    TARGET_SAMPLE_RATE,
    TARGET_CHANNELS,
)


# ── Helpers ───────────────────────────────────────────────────────────────────
def make_dummy_audio(
    duration_ms: int,
    sample_rate: int = 44100,
    channels: int = 2,
    format: str = 'wav',
    tmp_dir: str | None = None,
) -> str:
    """Create a synthetic test audio file (sine wave) and return its path."""
    audio = Sine(440).to_audio_segment(duration=duration_ms)
    audio = audio.set_frame_rate(sample_rate)
    if channels == 2:
        audio = audio.set_channels(2)

    suffix = f'.{format}'
    fd, path = tempfile.mkstemp(suffix=suffix, dir=tmp_dir)
    os.close(fd)
    audio.export(path, format=format)
    return path


# ── Tests ─────────────────────────────────────────────────────────────────────
class TestPreprocessor:

    def test_converts_stereo_44k_wav_to_mono_16k(self, tmp_path):
        """Standard 2-channel 44.1kHz WAV → mono 16kHz WAV"""
        in_path = make_dummy_audio(2000, sample_rate=44100, channels=2,
                                    format='wav', tmp_dir=str(tmp_path))

        result = preprocess_audio(in_path)

        assert os.path.exists(result['wav_path'])
        assert result['original_sample_rate'] == 44100
        assert result['original_channels']    == 2
        assert result['duration_sec']         == 2.0

        # Verify output is actually 16kHz mono
        out_audio = AudioSegment.from_wav(result['wav_path'])
        assert out_audio.frame_rate == TARGET_SAMPLE_RATE
        assert out_audio.channels   == TARGET_CHANNELS

    def test_passes_through_correct_format(self, tmp_path):
        """Already 16kHz mono WAV stays same shape"""
        in_path = make_dummy_audio(1500, sample_rate=16000, channels=1,
                                    format='wav', tmp_dir=str(tmp_path))

        result = preprocess_audio(in_path)

        out_audio = AudioSegment.from_wav(result['wav_path'])
        assert out_audio.frame_rate == 16000
        assert out_audio.channels   == 1

    def test_converts_mp3_format(self, tmp_path):
        """MP3 input → WAV output"""
        in_path = make_dummy_audio(1500, format='mp3', tmp_dir=str(tmp_path))

        result = preprocess_audio(in_path)

        assert result['original_format'] == '.mp3'
        assert result['wav_path'].endswith('.wav')
        assert os.path.exists(result['wav_path'])

    def test_custom_output_path(self, tmp_path):
        """Output path override works"""
        in_path  = make_dummy_audio(1000, tmp_dir=str(tmp_path))
        out_path = str(tmp_path / 'custom_output.wav')

        result = preprocess_audio(in_path, output_path=out_path)

        assert result['wav_path'] == out_path
        assert os.path.exists(out_path)

    def test_rejects_audio_too_short(self, tmp_path):
        """Audio < 0.5s → AudioTooShortError"""
        in_path = make_dummy_audio(200, tmp_dir=str(tmp_path))

        with pytest.raises(AudioTooShortError):
            preprocess_audio(in_path)

    def test_rejects_nonexistent_file(self):
        """Missing file → FileNotFoundError"""
        with pytest.raises(FileNotFoundError):
            preprocess_audio('/nonexistent/path/to/audio.wav')

    def test_returns_all_expected_fields(self, tmp_path):
        """Result dict has all required keys"""
        in_path = make_dummy_audio(1000, tmp_dir=str(tmp_path))

        result = preprocess_audio(in_path)

        for key in ('wav_path', 'duration_sec', 'original_sample_rate',
                    'original_channels', 'original_format', 'size_kb'):
            assert key in result

    def test_duration_accurate(self, tmp_path):
        """Duration field matches actual audio length"""
        in_path = make_dummy_audio(3500, tmp_dir=str(tmp_path))

        result = preprocess_audio(in_path)

        assert 3.4 <= result['duration_sec'] <= 3.6  # ~3.5s
