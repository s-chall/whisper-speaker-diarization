# 🎙️ Transcription Pipeline

A fully automated audio transcription tool that turns interviews, meetings, and conversations into clean, speaker-labeled transcripts — complete with timestamps. Built with OpenAI Whisper + pyannote.audio.

---

## ✨ What It Does

- 🎤 **Records audio** live from your microphone OR **loads any audio file** (MP3, M4A, WAV, etc.)
- 🗣️ **Speaker diarization** — identifies who said what and when using pyannote.audio
- 📝 **Transcribes speech to text** with timestamps using OpenAI Whisper
- 🔀 **Merges** transcription + diarization into a clean, readable transcript
- 💾 **Saves output** as a formatted `.pdf` with periodic timestamp markers and bold speaker labels

---

## 🚀 Quickstart

### 1. Clone the repo

```bash
git clone https://github.com/s-chall/whisper-speaker-diarization.git
cd whisper-speaker-diarization
```

### 2. Install dependencies

```bash
pip3 install -r requirements.txt
```

> ⚠️ You'll also need **ffmpeg** installed on your system for audio format conversion.
> - Mac: `brew install ffmpeg`
> - Linux: `sudo apt install ffmpeg`
> - Windows: [Download from ffmpeg.org](https://ffmpeg.org/download.html)

### 3. Set up your HuggingFace token

```bash
cp .env.example .env
```

Then edit `.env` and add your HuggingFace token:

```
HF_TOKEN=your_huggingface_token_here
```

> 🔑 Get a free token at [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)
>
> Then, in your HuggingFace account settings, you must **enable read permissions** for the following two models by accepting their terms:
> - [pyannote/speaker-diarization-3.1](https://huggingface.co/pyannote/speaker-diarization-3.1)
> - [pyannote/segmentation-3.0](https://huggingface.co/pyannote/segmentation-3.0)

---

## 🎬 Usage

**Transcribe an existing audio file**
```bash
python main.py --input path/to/interview.mp3
```

**Record directly from your microphone**
```bash
python main.py --record --duration 120
```

**Use a bigger Whisper model for better accuracy**
```bash
python main.py --input audio.mp3 --model medium
```

**Specify the number of speakers (improves diarization accuracy)**
```bash
python main.py --input interview.mp3 --speakers 2
```

**Full options**
```bash
python main.py --help
```

| Flag | Description | Default |
|------|-------------|---------|
| `--input` | Path to audio file | — |
| `--record` | Record from microphone | — |
| `--duration` | Recording duration (seconds) | 60 |
| `--model` | Whisper model size: `tiny`, `base`, `small`, `medium`, `large` | `base` |
| `--speakers` | Exact number of speakers | auto-detect |
| `--min-speakers` | Minimum speakers | — |
| `--max-speakers` | Maximum speakers | — |
| `--output-dir` | Directory for output files | `transcripts/` |
| `--name` | Base name for output files | `transcript` |
| `--clear` | Clear existing transcripts before running | `false` |

---

## 📄 Example Output

```
[00:00:01.200 --> 00:00:05.400] Speaker 1: So tell me a bit about your experience with the product.
[00:00:06.100 --> 00:00:14.800] Speaker 2: Yeah, honestly I found it really intuitive. The onboarding was smooth.
[00:00:15.200 --> 00:00:18.500] Speaker 1: That's great to hear. What would you change, if anything?
```

Transcripts are saved to `transcripts/transcript.pdf`.

---

## 🏗️ Project Structure

```
Transcription/
├── main.py              # Entry point & CLI
├── audio_handler.py     # Audio recording & file loading
├── transcriber.py       # Whisper speech-to-text
├── diarizer.py          # pyannote speaker diarization
├── pipeline.py          # Merges transcription + diarization
├── formatter.py         # Output formatting & file saving
├── requirements.txt     # Python dependencies
└── .env.example         # Environment variable template
```

---

## 🧠 How It Works

1. **Audio prep** — loads or records audio, converts to 16kHz mono WAV
2. **Diarization** — pyannote.audio identifies speaker turns with timestamps
3. **Transcription** — Whisper transcribes speech into text segments with timestamps
4. **Merging** — each text segment is matched to the speaker with the most overlapping time
5. **Output** — consecutive segments from the same speaker are merged, then saved

---

## ⚡ Model Size Guide

| Model | Speed | Accuracy | VRAM |
|-------|-------|----------|------|
| tiny | ⚡⚡⚡⚡ | ★★☆☆ | ~1 GB |
| base | ⚡⚡⚡ | ★★★☆ | ~1 GB |
| small | ⚡⚡ | ★★★☆ | ~2 GB |
| medium | ⚡ | ★★★★ | ~5 GB |
| large | 🐌 | ★★★★★ | ~10 GB |

For interview transcription, `base` or `small` works well. Use `medium` or `large` for noisy audio or heavy accents.

---

## 🛠️ Requirements

- Python 3.9+
- A HuggingFace account with read access granted to `pyannote/speaker-diarization-3.1` and `pyannote/segmentation-3.0`
- `ffmpeg` on your system PATH
- CUDA-capable GPU recommended (works on CPU but slower)

---

## 💡 Use Cases

- 🎓 Qualitative research interviews
- 📋 Meeting notes & minutes
- 🎙️ Podcast transcription
- 🗞️ Journalist interviews
- 📚 Oral history projects
- 🤝 User research sessions

---

## 📦 Dependencies

- [openai-whisper](https://github.com/openai/whisper) — speech-to-text
- [pyannote.audio](https://github.com/pyannote/pyannote-audio) — speaker diarization
- [torchaudio](https://pytorch.org/audio/) — audio processing
- [sounddevice](https://python-sounddevice.readthedocs.io/) — microphone recording

---

## 🤝 Contributing

PRs welcome. Open an issue or submit a pull request.

---

## 📜 License

MIT — use it, fork it, build on it.

---

*If this saved you hours of manual transcription, consider giving it a ⭐*
