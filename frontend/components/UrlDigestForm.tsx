"use client";

import { useState } from "react";
import useSWR from "swr";
import { getJobStatus, getReport, submitUrlDigest } from "@/lib/api";
import type { DigestReport } from "@/lib/types";
import { DigestReport as DigestReportComponent } from "./DigestReport";

const MAX_URLS = 20;

function validateUrls(raw: string): { valid: string[]; errors: string[] } {
  const lines = raw
    .split("\n")
    .map((l) => l.trim())
    .filter(Boolean);
  const errors: string[] = [];
  const valid: string[] = [];

  if (lines.length === 0) {
    errors.push("Enter at least one URL.");
    return { valid, errors };
  }
  if (lines.length > MAX_URLS) {
    errors.push(`Maximum ${MAX_URLS} URLs allowed (you entered ${lines.length}).`);
    return { valid, errors };
  }
  for (const line of lines) {
    if (!line.startsWith("http://") && !line.startsWith("https://")) {
      errors.push(`Invalid URL (must start with http:// or https://): ${line}`);
    } else {
      valid.push(line);
    }
  }
  return { valid, errors };
}

export function UrlDigestForm() {
  const [input, setInput] = useState("");
  const [errors, setErrors] = useState<string[]>([]);
  const [jobId, setJobId] = useState<string | null>(null);
  const [report, setReport] = useState<DigestReport | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const urlCount = input
    .split("\n")
    .map((l) => l.trim())
    .filter(Boolean).length;
  const isOverLimit = urlCount > MAX_URLS;

  const { data: jobData } = useSWR(
    jobId ? `/jobs/${jobId}` : null,
    () => getJobStatus(jobId!),
    {
      refreshInterval: (data) => {
        const s = data?.data?.status;
        return s === "queued" || s === "running" ? 3000 : 0;
      },
      async onSuccess(data) {
        if (data?.data?.status === "done") {
          const reportId = data.data.report_id;
          if (reportId) {
            const r = await getReport(reportId);
            if (r.data) setReport(r.data);
            else setSubmitError("Digest assembled but could not be loaded.");
          } else {
            setSubmitError("No articles could be fetched from the provided URLs.");
          }
          setJobId(null);
        }
        if (data?.data?.status === "failed") {
          setSubmitError(data.data.error_message ?? "Processing failed. Please try again.");
          setJobId(null);
        }
      },
    }
  );

  const isPolling =
    jobData?.data?.status === "queued" || jobData?.data?.status === "running";
  const isLoading = isSubmitting || isPolling;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErrors([]);
    setSubmitError(null);
    setReport(null);

    const { valid, errors: validationErrors } = validateUrls(input);
    if (validationErrors.length > 0) {
      setErrors(validationErrors);
      return;
    }

    setIsSubmitting(true);
    try {
      const res = await submitUrlDigest(valid);
      if (res.error) {
        setSubmitError(res.error);
      } else if (res.data) {
        setJobId(res.data.id);
      }
    } catch {
      setSubmitError("Failed to connect to the server.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label
            htmlFor="urls"
            className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
          >
            Article URLs{" "}
            <span
              className={`text-xs ${
                isOverLimit ? "text-red-500 font-semibold" : "text-gray-400"
              }`}
            >
              {urlCount} / {MAX_URLS}
            </span>
          </label>
          <textarea
            id="urls"
            value={input}
            onChange={(e) => {
              setInput(e.target.value);
              setErrors([]);
            }}
            placeholder={"https://example.com/article-1\nhttps://example.com/article-2"}
            rows={8}
            disabled={isLoading}
            className="w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm font-mono text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50"
          />
          <p className="mt-1 text-xs text-gray-400">One URL per line · max {MAX_URLS} URLs</p>
        </div>

        {errors.length > 0 && (
          <ul className="rounded-md bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 p-3 space-y-1">
            {errors.map((e, i) => (
              <li key={i} className="text-sm text-red-700 dark:text-red-400">
                {e}
              </li>
            ))}
          </ul>
        )}

        <button
          type="submit"
          disabled={isLoading || isOverLimit || !input}
          className="flex items-center gap-2 rounded-md bg-indigo-600 px-5 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isLoading && (
            <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8v8H4z"
              />
            </svg>
          )}
          {isLoading ? "Processing…" : "Summarize"}
        </button>
      </form>

      {submitError && (
        <p className="mt-6 text-sm text-red-600 dark:text-red-400">{submitError}</p>
      )}

      {report && (
        <div className="mt-8 border-t border-gray-200 dark:border-gray-700 pt-8">
          <DigestReportComponent report={report} />
        </div>
      )}
    </div>
  );
}
