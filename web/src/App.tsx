import { useEffect, useMemo, useRef, useState } from "react";
import {
  createJob,
  getHealth,
  getJob,
  pdfUrl,
  type JobStatus,
  type TranscriptEntry,
} from "./api";

const MODELS = ["tiny", "base", "small", "medium", "large"] as const;

const SPEAKER_COLORS = [
  "#2563eb",
  "#dc2626",
  "#059669",
  "#d97706",
  "#7c3aed",
  "#db2777",
  "#0891b2",
  "#65a30d",
];

function fmtTime(seconds: number): string {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.floor(seconds % 60);
  return h > 0
    ? `${h}:${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`
    : `${m}:${String(s).padStart(2, "0")}`;
}

function stageLabel(stage: string): string {
  switch (stage) {
    case "queued":
      return "Queued";
    case "converting":
      return "Preparing audio";
    case "diarizing":
      return "Identifying speakers";
    case "transcribing":
      return "Transcribing speech";
    case "merging":
      return "Merging segments";
    case "done":
      return "Complete";
    case "error":
      return "Error";
    default:
      return stage;
  }
}

export default function App() {
  const [file, setFile] = useState<File | null>(null);
  const [model, setModel] = useState<string>("base");
  const [name, setName] = useState<string>("transcript");
  const [speakers, setSpeakers] = useState<string>("");
  const [minSpeakers, setMinSpeakers] = useState<string>("");
  const [maxSpeakers, setMaxSpeakers] = useState<string>("");
  const [jobId, setJobId] = useState<string | null>(null);
  const [job, setJob] = useState<JobStatus | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [hfConfigured, setHfConfigured] = useState<boolean | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const pollRef = useRef<number | null>(null);

  useEffect(() => {
    getHealth()
      .then((h) => setHfConfigured(h.hf_token_configured))
      .catch(() => setHfConfigured(null));
  }, []);

  useEffect(() => {
    if (!jobId) return;
    let cancelled = false;

    const tick = async () => {
      try {
        const status = await getJob(jobId);
        if (cancelled) return;
        setJob(status);
        if (status.status === "done" || status.status === "error") {
          if (pollRef.current) window.clearInterval(pollRef.current);
          pollRef.current = null;
        }
      } catch (err) {
        console.error(err);
      }
    };

    tick();
    pollRef.current = window.setInterval(tick, 1500);
    return () => {
      cancelled = true;
      if (pollRef.current) {
        window.clearInterval(pollRef.current);
        pollRef.current = null;
      }
    };
  }, [jobId]);

  const speakerColorMap = useMemo(() => {
    const map: Record<string, string> = {};
    (job?.speakers ?? []).forEach((s, i) => {
      map[s] = SPEAKER_COLORS[i % SPEAKER_COLORS.length];
    });
    return map;
  }, [job?.speakers]);

  const disabled = submitting || (!!job && job.status === "running") || job?.status === "queued";

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!file) {
      setSubmitError("Please choose an audio file first.");
      return;
    }
    setSubmitError(null);
    setSubmitting(true);
    setJob(null);
    setJobId(null);
    try {
      const res = await createJob({
        file,
        model,
        name: name || "transcript",
        speakers: speakers ? Number(speakers) : undefined,
        minSpeakers: minSpeakers ? Number(minSpeakers) : undefined,
        maxSpeakers: maxSpeakers ? Number(maxSpeakers) : undefined,
      });
      setJobId(res.job_id);
    } catch (err) {
      setSubmitError(err instanceof Error ? err.message : String(err));
    } finally {
      setSubmitting(false);
    }
  }

  function handleDrop(e: React.DragEvent<HTMLLabelElement>) {
    e.preventDefault();
    setDragOver(false);
    const dropped = e.dataTransfer.files?.[0];
    if (dropped) setFile(dropped);
  }

  return (
    <div className="app">
      <header className="hero">
        <h1>Whisper + Speaker Diarization</h1>
        <p className="subtitle">
          Upload an audio file to generate a speaker-labeled transcript.
        </p>
        {hfConfigured === false && (
          <div className="banner banner-warn">
            HF_TOKEN is not configured on the server. Add it to <code>.env</code> and restart the API.
          </div>
        )}
      </header>

      <form className="card" onSubmit={handleSubmit}>
        <label
          className={`dropzone ${dragOver ? "dropzone-over" : ""} ${file ? "dropzone-filled" : ""}`}
          onDragOver={(e) => {
            e.preventDefault();
            setDragOver(true);
          }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
        >
          <input
            type="file"
            accept="audio/*,video/*,.mp3,.wav,.m4a,.flac,.ogg,.webm,.mp4"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          />
          {file ? (
            <div>
              <strong>{file.name}</strong>
              <div className="muted">{(file.size / (1024 * 1024)).toFixed(1)} MB — click to change</div>
            </div>
          ) : (
            <div>
              <strong>Drop an audio file here</strong>
              <div className="muted">or click to browse (MP3, M4A, WAV, FLAC, etc.)</div>
            </div>
          )}
        </label>

        <div className="grid">
          <div className="field">
            <label htmlFor="model">Whisper model</label>
            <select id="model" value={model} onChange={(e) => setModel(e.target.value)}>
              {MODELS.map((m) => (
                <option key={m} value={m}>
                  {m}
                </option>
              ))}
            </select>
            <span className="hint">Larger models are slower but more accurate.</span>
          </div>

          <div className="field">
            <label htmlFor="name">Output name</label>
            <input
              id="name"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="transcript"
            />
            <span className="hint">Used as the PDF filename.</span>
          </div>

          <div className="field">
            <label htmlFor="speakers">Exact speakers</label>
            <input
              id="speakers"
              type="number"
              min={1}
              value={speakers}
              onChange={(e) => setSpeakers(e.target.value)}
              placeholder="auto"
            />
            <span className="hint">Leave blank to auto-detect.</span>
          </div>

          <div className="field">
            <label htmlFor="minSpeakers">Min speakers</label>
            <input
              id="minSpeakers"
              type="number"
              min={1}
              value={minSpeakers}
              onChange={(e) => setMinSpeakers(e.target.value)}
              placeholder="—"
              disabled={!!speakers}
            />
          </div>

          <div className="field">
            <label htmlFor="maxSpeakers">Max speakers</label>
            <input
              id="maxSpeakers"
              type="number"
              min={1}
              value={maxSpeakers}
              onChange={(e) => setMaxSpeakers(e.target.value)}
              placeholder="—"
              disabled={!!speakers}
            />
          </div>
        </div>

        <div className="actions">
          <button type="submit" className="primary" disabled={disabled || !file}>
            {submitting ? "Uploading..." : "Transcribe"}
          </button>
          {submitError && <div className="error">{submitError}</div>}
        </div>
      </form>

      {job && <JobPanel job={job} />}

      {job?.status === "done" && job.transcript.length > 0 && (
        <Transcript entries={job.transcript} colorMap={speakerColorMap} jobId={job.id} />
      )}
    </div>
  );
}

function JobPanel({ job }: { job: JobStatus }) {
  const pct = Math.round(job.progress * 100);
  return (
    <div className="card status">
      <div className="status-row">
        <div>
          <div className="status-stage">{stageLabel(job.stage)}</div>
          <div className="muted">{job.message || "\u00a0"}</div>
        </div>
        <div className="status-pct">{pct}%</div>
      </div>
      <div className="progress">
        <div
          className={`progress-bar ${job.status === "error" ? "progress-bar-error" : ""}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      {job.status === "error" && job.error && <div className="error">{job.error}</div>}
    </div>
  );
}

function Transcript({
  entries,
  colorMap,
  jobId,
}: {
  entries: TranscriptEntry[];
  colorMap: Record<string, string>;
  jobId: string;
}) {
  return (
    <div className="card transcript">
      <div className="transcript-header">
        <h2>Transcript</h2>
        <a className="primary download" href={pdfUrl(jobId)} target="_blank" rel="noreferrer">
          Download PDF
        </a>
      </div>
      <div className="entries">
        {entries.map((entry, i) => (
          <div className="entry" key={i}>
            <div className="entry-meta">
              <span
                className="speaker"
                style={{ color: colorMap[entry.speaker] ?? "#111" }}
              >
                {entry.speaker}
              </span>
              <span className="timestamp">
                {fmtTime(entry.start)} – {fmtTime(entry.end)}
              </span>
            </div>
            <p className="text">{entry.text}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
