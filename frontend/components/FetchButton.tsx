"use client";

import { useState } from "react";
import useSWR, { useSWRConfig } from "swr";
import { getJobStatus, triggerFetch } from "@/lib/api";

export function FetchButton() {
  const [jobId, setJobId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const { mutate } = useSWRConfig();

  const { data: jobData } = useSWR(
    jobId ? `/jobs/${jobId}` : null,
    () => getJobStatus(jobId!),
    {
      refreshInterval: (data) =>
        data?.data?.status === "running" || data?.data?.status === "queued" ? 3000 : 0,
      onSuccess(data) {
        if (data?.data?.status === "done") {
          mutate("/api/reports/latest");
          setJobId(null);
        }
        if (data?.data?.status === "failed") {
          setError(data.data.error_message ?? "Fetch failed");
          setJobId(null);
        }
      },
    }
  );

  const status = jobData?.data?.status;
  const isLoading = status === "queued" || status === "running";

  async function handleClick() {
    setError(null);
    const res = await triggerFetch();
    if (res.error) {
      setError(res.error);
    } else if (res.data) {
      setJobId(res.data.id);
    }
  }

  return (
    <div className="flex flex-col items-center gap-2">
      <button
        onClick={handleClick}
        disabled={isLoading}
        className="flex items-center gap-2 rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {isLoading && (
          <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
          </svg>
        )}
        {isLoading ? "Fetching…" : "Fetch Now"}
      </button>
      {error && <p className="text-sm text-red-500">{error}</p>}
    </div>
  );
}
