"""Speaker assignment and segment merging for the transcription pipeline.

Bridges Whisper transcription segments with pyannote diarization segments by
matching them on time overlap, then collapses consecutive same-speaker turns
into single entries.
"""

from __future__ import annotations


def _overlap(a_start: float, a_end: float, b_start: float, b_end: float) -> float:
    """Return the duration of the overlap between two time intervals."""
    return max(0.0, min(a_end, b_end) - max(a_start, b_start))


def assign_speakers(
    transcription_segments: list[dict],
    diarization_segments: list[dict],
) -> list[dict]:
    """Assign a speaker label to every Whisper transcription segment.

    For each transcription segment the diarization segment with the greatest
    time overlap is selected.  When no overlap exists (e.g. the segment sits in
    a gap between diarization turns) the nearest segment boundary is used as a
    fallback so that every segment always receives a label.

    Args:
        transcription_segments: Output of transcriber.transcribe().
        diarization_segments: Output of diarizer.diarize() (after
            normalize_speaker_labels).

    Returns:
        A list of dicts with keys "start", "end", "speaker", and "text".
    """
    result = []
    for tseg in transcription_segments:
        t_start, t_end, text = tseg["start"], tseg["end"], tseg["text"]

        # Primary strategy: pick the diarization segment with most overlap
        best_speaker: str | None = None
        best_overlap = 0.0
        for dseg in diarization_segments:
            ov = _overlap(t_start, t_end, dseg["start"], dseg["end"])
            if ov > best_overlap:
                best_overlap = ov
                best_speaker = dseg["speaker"]

        # Fallback: assign to the nearest segment when there is no overlap
        if best_speaker is None and diarization_segments:
            t_mid = (t_start + t_end) / 2
            nearest = min(
                diarization_segments,
                key=lambda d: min(abs(t_mid - d["start"]), abs(t_mid - d["end"])),
            )
            best_speaker = nearest["speaker"]

        result.append(
            {
                "start": t_start,
                "end": t_end,
                "speaker": best_speaker or "Unknown",
                "text": text,
            }
        )
    return result


def merge_consecutive(entries: list[dict]) -> list[dict]:
    """Merge back-to-back entries from the same speaker into one entry.

    Args:
        entries: Output of assign_speakers().

    Returns:
        A new list where consecutive same-speaker entries are collapsed,
        with their text joined by a space and their end time extended.
    """
    if not entries:
        return []

    merged = [entries[0].copy()]
    for entry in entries[1:]:
        last = merged[-1]
        if entry["speaker"] == last["speaker"]:
            last["end"] = entry["end"]
            last["text"] = f"{last['text']} {entry['text']}"
        else:
            merged.append(entry.copy())
    return merged
