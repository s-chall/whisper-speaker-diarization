"""Speaker diarization utilities using pyannote.audio.

Wraps the pyannote speaker-diarization-3.1 pipeline to produce time-stamped,
speaker-labelled segments from an audio file.
"""

from __future__ import annotations

from pyannote.audio import Pipeline
from pyannote.core import Annotation


def load_diarization_pipeline(hf_token: str) -> Pipeline:
    """Load the pyannote speaker-diarization pipeline from HuggingFace.

    Args:
        hf_token: A HuggingFace access token with access to the
            pyannote/speaker-diarization-3.1 model.

    Returns:
        A ready-to-use pyannote Pipeline instance.
    """
    return Pipeline.from_pretrained(
        "pyannote/speaker-diarization-3.1",
        token=hf_token,
    )


def diarize(
    pipeline: Pipeline,
    audio_path: str,
    num_speakers: int | None = None,
    min_speakers: int | None = None,
    max_speakers: int | None = None,
) -> list[dict]:
    """Run speaker diarization on an audio file.

    Exactly one of num_speakers (precise count) or the min/max pair should be
    provided for best accuracy.  If none are given, pyannote estimates the
    number automatically.

    Args:
        pipeline: A loaded pyannote Pipeline instance.
        audio_path: Path to the audio file to diarize.
        num_speakers: Exact number of speakers (overrides min/max).
        min_speakers: Lower bound on the expected speaker count.
        max_speakers: Upper bound on the expected speaker count.

    Returns:
        A list of dicts with keys "start" (float), "end" (float), and
        "speaker" (str), sorted by start time.
    """
    kwargs: dict = {}
    if num_speakers is not None:
        kwargs["num_speakers"] = num_speakers
    else:
        if min_speakers is not None:
            kwargs["min_speakers"] = min_speakers
        if max_speakers is not None:
            kwargs["max_speakers"] = max_speakers

    raw = pipeline(audio_path, **kwargs)
    diarization: Annotation = getattr(raw, "speaker_diarization", raw)

    segments = [
        {
            "start": round(turn.start, 3),
            "end": round(turn.end, 3),
            "speaker": speaker,
        }
        for turn, _, speaker in diarization.itertracks(yield_label=True)
    ]
    segments.sort(key=lambda s: s["start"])
    return segments


def normalize_speaker_labels(segments: list[dict]) -> list[dict]:
    """Re-label raw pyannote speaker IDs as sequential "Speaker N" strings.

    pyannote returns opaque labels like "SPEAKER_00".  This function maps them
    to human-friendly names in order of first appearance.

    Args:
        segments: List of diarization dicts (mutated in place).

    Returns:
        The same list with "speaker" values replaced.
    """
    label_map: dict[str, str] = {}
    for seg in segments:
        raw = seg["speaker"]
        if raw not in label_map:
            label_map[raw] = f"Speaker {len(label_map) + 1}"
        seg["speaker"] = label_map[raw]
    return segments
