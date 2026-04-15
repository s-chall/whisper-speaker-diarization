def _overlap(a_start: float, a_end: float, b_start: float, b_end: float) -> float:
    return max(0.0, min(a_end, b_end) - max(a_start, b_start))


def assign_speakers(
    transcription_segments: list[dict],
    diarization_segments: list[dict],
) -> list[dict]:
    result = []
    for tseg in transcription_segments:
        t_start, t_end, text = tseg["start"], tseg["end"], tseg["text"]

        best_speaker = None
        best_overlap = 0.0
        for dseg in diarization_segments:
            ov = _overlap(t_start, t_end, dseg["start"], dseg["end"])
            if ov > best_overlap:
                best_overlap = ov
                best_speaker = dseg["speaker"]

        if best_speaker is None and diarization_segments:
            t_mid = (t_start + t_end) / 2
            best_speaker = min(
                diarization_segments,
                key=lambda d: min(
                    abs(t_mid - d["start"]),
                    abs(t_mid - d["end"]),
                )
            )["speaker"]

        result.append({
            "start": t_start,
            "end": t_end,
            "speaker": best_speaker or "Unknown",
            "text": text,
        })
    return result


def merge_consecutive(entries: list[dict]) -> list[dict]:
    if not entries:
        return []
    merged = [entries[0].copy()]
    for entry in entries[1:]:
        last = merged[-1]
        if entry["speaker"] == last["speaker"]:
            last["end"] = entry["end"]
            last["text"] = last["text"] + " " + entry["text"]
        else:
            merged.append(entry.copy())
    return merged
