"""Audio recording and loading utilities for the transcription pipeline.

Handles microphone input (via sounddevice) and converts arbitrary audio files
to the 16 kHz mono WAV format expected by Whisper and pyannote.
"""

import os
import queue
import wave

import sounddevice as sd
import torchaudio


SAMPLE_RATE: int = 16_000  # Hz - required by both Whisper and pyannote
CHANNELS: int = 1          # Mono
CHUNK_SIZE: int = 1024     # Frames per sounddevice callback


def record_audio(output_path: str, duration: int) -> str:
    """Record audio from the default microphone and save it as a WAV file.

    Args:
        output_path: Destination path for the recorded WAV file.
        duration: Recording length in seconds.

    Returns:
        The path to the saved WAV file.
    """
    print(f"Recording for {duration} second(s) - stops automatically.")
    audio_queue: queue.Queue = queue.Queue()

    def _callback(indata, frames, time, status):  # noqa: ARG001
        audio_queue.put(indata.copy())

    parent_dir = os.path.dirname(output_path) or "."
    os.makedirs(parent_dir, exist_ok=True)

    with wave.open(output_path, "wb") as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(2)  # 16-bit PCM: 2 bytes per sample
        wf.setframerate(SAMPLE_RATE)

        with sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype="int16",
            blocksize=CHUNK_SIZE,
            callback=_callback,
        ):
            total_frames = duration * SAMPLE_RATE
            recorded = 0
            while recorded < total_frames:
                chunk = audio_queue.get()
                chunk = chunk[: total_frames - recorded]
                wf.writeframes(chunk.tobytes())
                recorded += len(chunk)

    print(f"Saved recording to: {output_path}")
    return output_path


def load_audio(input_path: str, output_dir: str = "audio") -> str:
    """Load an audio file and convert it to 16 kHz mono WAV if necessary.

    Handles any format supported by torchaudio (MP3, M4A, FLAC, etc.) and
    resamples / downmixes to meet Whisper's expected input format.

    Args:
        input_path: Path to the source audio file.
        output_dir: Directory in which to save the converted WAV file.

    Returns:
        The path to the converted WAV file.
    """
    os.makedirs(output_dir, exist_ok=True)
    stem = os.path.splitext(os.path.basename(input_path))[0]
    output_path = os.path.join(output_dir, f"{stem}_converted.wav")

    waveform, sample_rate = torchaudio.load(input_path)

    # Downmix to mono if the source is multi-channel
    if waveform.shape[0] > 1:
        waveform = waveform.mean(dim=0, keepdim=True)

    # Resample only when the source rate differs from the target
    if sample_rate != SAMPLE_RATE:
        resampler = torchaudio.transforms.Resample(
            orig_freq=sample_rate, new_freq=SAMPLE_RATE
        )
        waveform = resampler(waveform)

    torchaudio.save(output_path, waveform, SAMPLE_RATE)
    print(f"Converted and saved to: {output_path}")
    return output_path
