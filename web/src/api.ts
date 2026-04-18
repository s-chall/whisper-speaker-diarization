export type TranscriptEntry = {
  start: number;
  end: number;
  speaker: string;
  text: string;
};

export type JobStatus = {
  id: string;
  status: "queued" | "running" | "done" | "error";
  stage: string;
  progress: number;
  message: string;
  error: string | null;
  transcript: TranscriptEntry[];
  speakers: string[];
  base_name: string;
  has_pdf: boolean;
};

export type CreateJobParams = {
  file: File;
  model: string;
  name: string;
  speakers?: number;
  minSpeakers?: number;
  maxSpeakers?: number;
};

export async function createJob(params: CreateJobParams): Promise<{ job_id: string }> {
  const form = new FormData();
  form.append("file", params.file);
  form.append("model", params.model);
  form.append("name", params.name);
  if (params.speakers != null) form.append("speakers", String(params.speakers));
  if (params.minSpeakers != null) form.append("min_speakers", String(params.minSpeakers));
  if (params.maxSpeakers != null) form.append("max_speakers", String(params.maxSpeakers));

  const res = await fetch("/api/jobs", { method: "POST", body: form });
  if (!res.ok) {
    const msg = await res.text();
    throw new Error(msg || `Failed to create job (${res.status})`);
  }
  return res.json();
}

export async function getJob(jobId: string): Promise<JobStatus> {
  const res = await fetch(`/api/jobs/${jobId}`);
  if (!res.ok) throw new Error(`Failed to fetch job (${res.status})`);
  return res.json();
}

export function pdfUrl(jobId: string): string {
  return `/api/jobs/${jobId}/pdf`;
}

export async function getHealth(): Promise<{ status: string; hf_token_configured: boolean; models: string[] }> {
  const res = await fetch("/api/health");
  if (!res.ok) throw new Error("Health check failed");
  return res.json();
}
