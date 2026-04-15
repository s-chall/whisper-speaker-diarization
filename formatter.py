"""Transcript formatting and persistence utilities.

Converts the list of labelled segments produced by the pipeline into a
human-readable text representation and saves both plain-text and JSON copies
to disk.
"""

from __future__ import annotations

import json
import os


def _fmt_time(seconds: float) -> str:
    """Format a duration in seconds as HH:MM:SS.mmm.

    Args:
        seconds: Non-negative duration in seconds.

    Returns:
        A string in the form "HH:MM:SS.mmm".
    """
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}"


def format_transcript(entries: list[dict]) -> str:
    """Render a list of speaker-labelled segments as a readable string.

    Each entry produces two lines: a header with the timestamp range and
    speaker name, followed by the spoken text indented by two spaces.  Entries
    are separated by a blank line.

    Args:
        entries: Output of pipeline.merge_consecutive().

    Returns:
        A formatted multi-line string ready to display or write to a file.
    """
    lines = []
    for entry in entries:
        timestamp = f"[{_fmt_time(entry['start'])} --> {_fmt_time(entry['end'])}]"
        lines.append(f"{timestamp} {entry['speaker']}:")
        lines.append(f"  {entry['text']}")
        lines.append("")
    return "\n".join(lines)


def clear_transcripts(output_dir: str = "transcripts") -> None:
    """Delete all .txt and .json files in the transcript output directory.

    Args:
        output_dir: Path to the directory to clear.
    """
    if not os.path.exists(output_dir):
        print(f"No transcripts directory found at '{output_dir}', nothing to clear.")
        return

    removed = [
        filename
        for filename in os.listdir(output_dir)
        if filename.endswith((".txt", ".json"))
    ]
    for filename in removed:
        os.remove(os.path.join(output_dir, filename))

    if removed:
        file_list = "\n".join(f"  - {f}" for f in removed)
        print(f"Cleared {len(removed)} transcript file(s) from '{output_dir}':\n{file_list}")
    else:
        print(f"No transcript files found in '{output_dir}'.")


def save_transcript(
    entries: list[dict],
    output_dir: str = "transcripts",
    base_name: str = "transcript",
) -> tuple[str, str]:
    """Write the transcript to disk as both a .txt and a .json file.

    Args:
        entries: Output of pipeline.merge_consecutive().
        output_dir: Directory in which to create the output files.
        base_name: Filename stem (without extension) for both files.

    Returns:
        A tuple of (txt_path, json_path) for the files that were written.
    """
    os.makedirs(output_dir, exist_ok=True)
    txt_path = os.path.join(output_dir, f"{base_name}.txt")
    json_path = os.path.join(output_dir, f"{base_name}.json")

    with open(txt_path, "w", encoding="utf-8") as fh:
        fh.write(format_transcript(entries))
    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump(entries, fh, indent=2, ensure_ascii=False)

    print(f"Transcript saved:\n  {txt_path}\n  {json_path}")
    return txt_path, json_path
