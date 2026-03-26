import type { ApiResponse, DigestReport, DigestReportListItem, FetchJobOut, Source, SourceCreate, SourceUpdate, TopicFilter, TopicFilterCreate } from "./types";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function apiFetch<T>(path: string, options?: RequestInit): Promise<ApiResponse<T>> {
  const res = await fetch(`${BASE_URL}/api${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  return res.json() as Promise<ApiResponse<T>>;
}

export const getLatestReport = () =>
  apiFetch<DigestReport>("/reports/latest");

export const listReports = () =>
  apiFetch<DigestReportListItem[]>("/reports");

export const triggerFetch = () =>
  apiFetch<FetchJobOut>("/fetch", { method: "POST" });

export const getJobStatus = (jobId: string) =>
  apiFetch<FetchJobOut>(`/jobs/${jobId}`);

export const getSources = () =>
  apiFetch<Source[]>("/sources");

export const createSource = (body: SourceCreate) =>
  apiFetch<Source>("/sources", { method: "POST", body: JSON.stringify(body) });

export const updateSource = (id: string, body: SourceUpdate) =>
  apiFetch<Source>(`/sources/${id}`, { method: "PATCH", body: JSON.stringify(body) });

export const deleteSource = (id: string) =>
  apiFetch<Source>(`/sources/${id}`, { method: "DELETE" });

export const getTopics = () =>
  apiFetch<TopicFilter[]>("/topics");

export const createTopic = (body: TopicFilterCreate) =>
  apiFetch<TopicFilter>("/topics", { method: "POST", body: JSON.stringify(body) });

export const deleteTopic = (id: string) =>
  apiFetch<null>(`/topics/${id}`, { method: "DELETE" });

export const submitUrlDigest = (urls: string[]) =>
  apiFetch<FetchJobOut>("/url-digest", { method: "POST", body: JSON.stringify({ urls }) });

export const getReport = (reportId: string) =>
  apiFetch<DigestReport>(`/reports/${reportId}`);
