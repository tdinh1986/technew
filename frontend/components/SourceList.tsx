"use client";

import { useState } from "react";
import useSWR from "swr";
import { createSource, deleteSource, getSources, updateSource } from "@/lib/api";
import type { Source } from "@/lib/types";

const TYPE_LABELS: Record<string, string> = {
  rss: "RSS",
  newsapi: "NewsAPI",
  hackernews: "HN",
};

export function SourceList() {
  const { data: resp, mutate } = useSWR("sources", getSources);
  const sources = resp?.data ?? [];

  const [url, setUrl] = useState("");
  const [addError, setAddError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleAdd(e: React.FormEvent) {
    e.preventDefault();
    setAddError(null);
    setSubmitting(true);
    try {
      const result = await createSource({ type: "rss", url: url.trim() });
      if (result.error) {
        setAddError(result.error);
      } else {
        setUrl("");
        await mutate();
      }
    } finally {
      setSubmitting(false);
    }
  }

  async function handleToggle(source: Source) {
    await updateSource(source.id, { enabled: !source.enabled });
    await mutate();
  }

  async function handleDelete(source: Source) {
    await deleteSource(source.id);
    await mutate();
  }

  return (
    <div className="space-y-4">
      <ul className="divide-y divide-gray-200 dark:divide-gray-800">
        {sources.length === 0 && (
          <li className="py-3 text-sm text-gray-500">No sources yet.</li>
        )}
        {sources.map((source) => (
          <li key={source.id} className="flex items-center justify-between py-3 gap-3">
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium">
                {source.name ?? source.url}
              </p>
              <p className="truncate text-xs text-gray-500">{source.url}</p>
            </div>
            <span className="shrink-0 rounded px-1.5 py-0.5 text-xs font-mono bg-gray-100 dark:bg-gray-800">
              {TYPE_LABELS[source.type] ?? source.type}
            </span>
            <button
              onClick={() => handleToggle(source)}
              className={`shrink-0 text-xs px-2 py-1 rounded border ${
                source.enabled
                  ? "border-green-500 text-green-600 dark:text-green-400"
                  : "border-gray-300 text-gray-400"
              }`}
              aria-label={source.enabled ? "Disable source" : "Enable source"}
            >
              {source.enabled ? "Active" : "Inactive"}
            </button>
            <button
              onClick={() => handleDelete(source)}
              className="shrink-0 text-xs text-red-500 hover:text-red-700"
              aria-label="Remove source"
            >
              Remove
            </button>
          </li>
        ))}
      </ul>

      <form onSubmit={handleAdd} className="flex gap-2">
        <input
          type="url"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://example.com/feed.rss"
          required
          className="flex-1 rounded border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button
          type="submit"
          disabled={submitting}
          className="shrink-0 rounded bg-blue-600 px-3 py-1.5 text-sm text-white hover:bg-blue-700 disabled:opacity-50"
        >
          {submitting ? "Adding…" : "Add RSS"}
        </button>
      </form>
      {addError && (
        <p className="text-sm text-red-600 dark:text-red-400">{addError}</p>
      )}
    </div>
  );
}
