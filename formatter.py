import json
import os


def _fmt_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}"


def format_transcript(entries: list[dict]) -> str:
    lines = []
    for entry in entries:
        timestamp = f"[{_fmt_time(entry['start'])} --> {_fmt_time(entry['end'])}]"
        lines.append(f"{timestamp} {entry['speaker']}:")
        lines.append(f"  {entry['text']}")
        lines.append("")
    return "\n".join(lines)


def clear_transcripts(output_dir: str = "transcripts") -> None:
    if not os.path.exists(output_dir):
        print(f"No transcripts directory found at '{output_dir}', nothing to clear.")
        return
    removed = []
    for filename in os.listdir(output_dir):
        if filename.endswith(".txt") or filename.endswith(".json"):
            filepath = os.path.join(output_dir, filename)
            os.remove(filepath)
            removed.append(filename)
    if removed:
        print(f"Cleared {len(removed)} transcript file(s) from '{output_dir}':")
        for f in removed:
            print(f"  - {f}")
    else:
        print(f"No transcript files found in '{output_dir}'.")


def save_transcript(entries: list[dict], output_dir: str = "transcripts", base_name: str = "transcript"):
    os.makedirs(output_dir, exist_ok=True)
    txt_path = os.path.join(output_dir, f"{base_name}.txt")
    json_path = os.path.join(output_dir, f"{base_name}.json")

    readable = format_transcript(entries)
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(readable)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)

    print(f"Transcript saved:\n  {txt_path}\n  {json_path}")
    return txt_path, json_path
