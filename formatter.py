"""Transcript formatting and PDF persistence utilities."""

from __future__ import annotations

import os

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer


def _fmt_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}"


def _fmt_marker(seconds: float) -> str:
    """Format seconds as [H:MM:SS] for PDF timestamp markers."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"[{h}:{m:02d}:{s:02d}]"


def format_transcript(entries: list[dict]) -> str:
    """Render entries as a readable string for console output."""
    lines = []
    for entry in entries:
        timestamp = f"[{_fmt_time(entry['start'])} --> {_fmt_time(entry['end'])}]"
        lines.append(f"{timestamp} {entry['speaker']}:")
        lines.append(f"  {entry['text']}")
        lines.append("")
    return "\n".join(lines)


def clear_transcripts(output_dir: str = "transcripts") -> None:
    """Delete all .pdf files in the transcript output directory."""
    if not os.path.exists(output_dir):
        print(f"No transcripts directory found at '{output_dir}', nothing to clear.")
        return

    removed = [
        filename
        for filename in os.listdir(output_dir)
        if filename.endswith(".pdf")
    ]
    for filename in removed:
        os.remove(os.path.join(output_dir, filename))

    if removed:
        file_list = "\n".join(f"  - {f}" for f in removed)
        print(f"Cleared {len(removed)} transcript file(s) from '{output_dir}':\n{file_list}")
    else:
        print(f"No transcript files found in '{output_dir}'.")


def save_pdf(
    entries: list[dict],
    output_dir: str = "transcripts",
    base_name: str = "transcript",
    timestamp_interval: float = 30.0,
) -> str:
    """Write the transcript to disk as a PDF.

    The format mirrors research interview transcription style:
      - Periodic [H:MM:SS] timestamp markers (every ~30 s by default)
      - Speaker N: text lines

    Args:
        entries: Output of pipeline.merge_consecutive().
        output_dir: Directory in which to create the output file.
        base_name: Filename stem (without extension).
        timestamp_interval: Minimum seconds between timestamp markers.

    Returns:
        Path to the saved PDF file.
    """
    os.makedirs(output_dir, exist_ok=True)
    pdf_path = os.path.join(output_dir, f"{base_name}.pdf")

    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        leftMargin=1 * inch,
        rightMargin=1 * inch,
        topMargin=1 * inch,
        bottomMargin=1 * inch,
    )

    timestamp_style = ParagraphStyle(
        "Timestamp",
        fontName="Helvetica",
        fontSize=9,
        textColor=HexColor("#666666"),
        spaceBefore=14,
        spaceAfter=4,
    )
    speaker_style = ParagraphStyle(
        "Speaker",
        fontName="Helvetica",
        fontSize=11,
        leading=17,
        spaceAfter=5,
    )

    story = []
    last_marker_time = -timestamp_interval

    for entry in entries:
        if entry["start"] - last_marker_time >= timestamp_interval:
            story.append(Paragraph(_fmt_marker(entry["start"]), timestamp_style))
            last_marker_time = entry["start"]

        label = f"<b>{entry['speaker']}:</b> {entry['text']}"
        story.append(Paragraph(label, speaker_style))

    doc.build(story)
    print(f"Transcript saved: {pdf_path}")
    return pdf_path
