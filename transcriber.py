"""Whisper-based transcription utilities for the transcription pipeline."""

import whisper


def load_whisper_model(model_size: str = "base") -> whisper.Whisper:
    """Load and return a Whisper model of the requested size.

    Args:
        model_size: One of "tiny", "base", "small", "medium", or "large".

    Returns:
        A loaded Whisper model ready for inference.
    """
    print(f"Loading Whisper model: {model_size}")
    return whisper.load_model(model_size)


def transcribe(model: whisper.Whisper, audio_path: str) -> list[dict]:
    """Transcribe an audio file and return time-stamped segments.

    Args:
        model: A loaded Whisper model instance.
        audio_path: Path to the audio file to transcribe.

    Returns:
        A list of dicts with keys "start" (float), "end" (float), and
        "text" (str), one per Whisper segment.
    """
    result = model.transcribe(audio_path, word_timestamps=True, verbose=False)
    return [
        {
            "start": round(seg["start"], 3),
            "end": round(seg["end"], 3),
            "text": seg["text"].strip(),
        }
        for seg in result["segments"]
    ]
