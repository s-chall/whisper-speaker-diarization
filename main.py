import argparse
import os
from dotenv import load_dotenv

from audio_handler import record_audio, load_audio
from diarizer import load_diarization_pipeline, diarize, normalize_speaker_labels
from transcriber import load_whisper_model, transcribe
from pipeline import assign_speakers, merge_consecutive
from formatter import format_transcript, save_transcript, clear_transcripts

load_dotenv()


def parse_args():
    parser = argparse.ArgumentParser(description="Audio transcription with speaker diarization")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--input", type=str, help="Path to an existing audio file")
    group.add_argument("--record", action="store_true", help="Record from microphone")
    parser.add_argument("--duration", type=int, default=60, help="Recording duration in seconds (default: 60)")
    parser.add_argument("--model", type=str, default="base", choices=["tiny", "base", "small", "medium", "large"],
                        help="Whisper model size (default: base)")
    parser.add_argument("--output-dir", type=str, default="transcripts", help="Directory to save transcript files")
    parser.add_argument("--name", type=str, default="transcript", help="Base name for output files")
    parser.add_argument("--clear", action="store_true", help="Clear existing transcript files before running")
    parser.add_argument("--speakers", type=int, default=None, help="Exact number of speakers (most accurate when known)")
    parser.add_argument("--min-speakers", type=int, default=None, help="Minimum number of speakers")
    parser.add_argument("--max-speakers", type=int, default=None, help="Maximum number of speakers")
    return parser.parse_args()


def main():
    args = parse_args()

    hf_token = os.getenv("HF_TOKEN")
    if not hf_token:
        raise EnvironmentError(
            "HuggingFace token not found. Set HF_TOKEN in a .env file or as an environment variable.\n"
            "You need access to: https://huggingface.co/pyannote/speaker-diarization-3.1"
        )

    if args.clear:
        clear_transcripts(args.output_dir)

    os.makedirs("audio", exist_ok=True)
    if args.record:
        audio_path = record_audio(f"audio/{args.name}.wav", args.duration)
    else:
        audio_path = load_audio(args.input, output_dir="audio")

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
    print(f"Found {len(set(s['speaker'] for s in diar_segments))} speaker(s).")

    print("Running transcription...")
    whisper_model = load_whisper_model(args.model)
    transcription_segments = transcribe(whisper_model, audio_path)

    merged = assign_speakers(transcription_segments, diar_segments)
    merged = merge_consecutive(merged)

    print("\n--- TRANSCRIPT ---\n")
    print(format_transcript(merged))
    save_transcript(merged, output_dir=args.output_dir, base_name=args.name)


if __name__ == "__main__":
    main()
