import os
from pyannote.audio import Pipeline
from pyannote.core import Annotation


def load_diarization_pipeline(hf_token: str) -> Pipeline:
    pipeline = Pipeline.from_pretrained(
        "pyannote/speaker-diarization-3.1",
        use_auth_token=hf_token,
    )
    return pipeline


def diarize(pipeline: Pipeline, audio_path: str, num_speakers: int = None, min_speakers: int = None, max_speakers: int = None) -> list[dict]:
    kwargs = {}
    if num_speakers is not None:
        kwargs["num_speakers"] = num_speakers
    else:
        if min_speakers is not None:
            kwargs["min_speakers"] = min_speakers
        if max_speakers is not None:
            kwargs["max_speakers"] = max_speakers

    diarization: Annotation = pipeline(audio_path, **kwargs)

    segments = []
    for turn, _, speaker in diarization.itertracks(yield_label=True):
        segments.append({
            "start": round(turn.start, 3),
            "end": round(turn.end, 3),
            "speaker": speaker,
        })

    segments.sort(key=lambda s: s["start"])
    return segments


def normalize_speaker_labels(segments: list[dict]) -> list[dict]:
    label_map = {}
    counter = 1
    for seg in segments:
        raw = seg["speaker"]
        if raw not in label_map:
            label_map[raw] = f"Speaker {counter}"
            counter += 1
        seg["speaker"] = label_map[raw]
    return segments
