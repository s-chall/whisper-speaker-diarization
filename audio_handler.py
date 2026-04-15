import os
import wave
import queue
import numpy as np
import sounddevice as sd
import torchaudio
import torch

SAMPLE_RATE = 16000
CHANNELS = 1
CHUNK_SIZE = 1024


def record_audio(output_path: str, duration: int) -> str:
    print(f"Recording for {duration} seconds... (press nothing, it stops automatically)")
    audio_queue: queue.Queue = queue.Queue()

    def callback(indata, frames, time, status):
        audio_queue.put(indata.copy())

    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)

    with wave.open(output_path, "wb") as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)

        with sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype="int16",
            blocksize=CHUNK_SIZE,
            callback=callback,
        ):
            total_frames = int(duration * SAMPLE_RATE)
            recorded = 0
            while recorded < total_frames:
                chunk = audio_queue.get()
                remaining = total_frames - recorded
                chunk = chunk[:remaining]
                wf.writeframes(chunk.tobytes())
                recorded += len(chunk)

    print(f"Saved recording to: {output_path}")
    return output_path


def load_audio(input_path: str, output_dir: str = "audio") -> str:
    os.makedirs(output_dir, exist_ok=True)
    base = os.path.splitext(os.path.basename(input_path))[0]
    output_path = os.path.join(output_dir, f"{base}_converted.wav")

    waveform, sr = torchaudio.load(input_path)

    if waveform.shape[0] > 1:
        waveform = waveform.mean(dim=0, keepdim=True)

    if sr != SAMPLE_RATE:
        resampler = torchaudio.transforms.Resample(orig_freq=sr, new_freq=SAMPLE_RATE)
        waveform = resampler(waveform)

    torchaudio.save(output_path, waveform, SAMPLE_RATE)
    print(f"Converted and saved to: {output_path}")
    return output_path
