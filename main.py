"""Entry point for the audio transcription CLI.

Usage examples
--------------
Transcribe an existing file::

    python main.py --input interview.mp3 --speakers 2

Record from the microphone for 90 seconds::

    python main.py --record --duration 90 --name meeting --model small
"""

from __future__ import annotations

import argparse
import os

from dotenv import load_dotenv

from audio_handler import load_audio, record_audio
from diarizer import diarize, load_diarization_pipeline, normalize_speaker_labels
from formatter import clear_transcripts, format_transcript, save_pdf
from pipeline import assign_speakers, merge_consecutive
from transcriber import load_whisper_model, transcribe

load_dotenv()

_AUDIO_DIR = "audio"
_MODEL_CHOICES = ["tiny", "base", "small", "medium", "large"]


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Transcribe audio with per-speaker labels."
    )

    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--input", type=str, help="Path to an existing audio file.")
    source.add_argument("--record", action="store_true", help="Record from the microphone.")

    parser.add_argument(
        "--duration",
        type=int,
        default=60,
        help="Recording duration in seconds (default: 60). Only used with --record.",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="base",
        choices=_MODEL_CHOICES,
        help="Whisper model size (default: base). Larger models are slower but more accurate.",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="transcripts",
        help="Directory for output transcript files (default: transcripts).",
    )
    parser.add_argument(
        "--name",
        type=str,
        default="transcript",
        help="Base filename (without extension) for output files (default: transcript).",
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Remove existing transcript files before running.",
    )
    parser.add_argument(
        "--speakers",
        type=int,
        default=None,
        help="Exact number of speakers. Improves diarization accuracy when known.",
    )
    parser.add_argument(
        "--min-speakers",
        type=int,
        default=None,
        help="Minimum number of speakers (ignored when --speakers is set).",
    )
    parser.add_argument(
        "--max-speakers",
        type=int,
        default=None,
        help="Maximum number of speakers (ignored when --speakers is set).",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()

    hf_token = os.getenv("HF_TOKEN")
    if not hf_token:
        raise EnvironmentError(
            "HuggingFace token not found. Set HF_TOKEN in a .env file or as an "
            "environment variable.\n"
            "You need model access at: https://huggingface.co/pyannote/speaker-diarization-3.1"
        )

    if args.clear:
        clear_transcripts(args.output_dir)

    os.makedirs(_AUDIO_DIR, exist_ok=True)
    if args.record:
        audio_path = record_audio(f"{_AUDIO_DIR}/{args.name}.wav", args.duration)
    else:
        audio_path = load_audio(args.input, output_dir=_AUDIO_DIR)

    print("Running speaker diarization...")
    diar_pipeline = load_diarization_pipeline(hf_token)
    diar_segments = diarize(
        diar_pipeline,
        audio_path,
        num_speakers=args.speakers,
        min_speakers=args.min_speakers,
        max_speakers=args.max_speakers,
    )
    diar_segments = normalize_speaker_labels(diar_segments)
    n_speakers = len({s["speaker"] for s in diar_segments})
    print(f"Found {n_speakers} speaker(s).")
    if n_speakers == 0:
        print("Warning: no speakers detected — transcript will be empty.")

    print("Running transcription...")
    whisper_model = load_whisper_model(args.model)
    transcription_segments = transcribe(whisper_model, audio_path)
    if not transcription_segments:
        print("Warning: no speech detected in audio — transcript will be empty.")

    merged = merge_consecutive(assign_speakers(transcription_segments, diar_segments))

    print("\n--- TRANSCRIPT ---\n")
    print(format_transcript(merged))
    save_pdf(merged, output_dir=args.output_dir, base_name=args.name)


if __name__ == "__main__":
    main()
