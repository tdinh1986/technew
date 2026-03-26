"use client";

import { useState } from "react";
import useSWR from "swr";
import { createTopic, deleteTopic, getTopics } from "@/lib/api";

export function TopicList() {
  const { data: resp, mutate } = useSWR("topics", getTopics);
  const topics = resp?.data ?? [];

  const [keyword, setKeyword] = useState("");
  const [addError, setAddError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleAdd(e: React.FormEvent) {
    e.preventDefault();
    setAddError(null);
    setSubmitting(true);
    try {
      const result = await createTopic({ keyword: keyword.trim() });
      if (result.error) {
        setAddError(result.error);
      } else {
        setKeyword("");
        await mutate();
      }
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDelete(id: string) {
    await deleteTopic(id);
    await mutate();
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2">
        {topics.length === 0 && (
          <p className="text-sm text-gray-500">No topic filters yet.</p>
        )}
        {topics.map((topic) => (
          <span
            key={topic.id}
            className="inline-flex items-center gap-1.5 rounded-full bg-blue-100 dark:bg-blue-900 px-3 py-1 text-sm text-blue-800 dark:text-blue-200"
          >
            {topic.keyword}
            <button
              onClick={() => handleDelete(topic.id)}
              className="text-blue-500 hover:text-blue-700 dark:hover:text-blue-300"
              aria-label={`Remove topic ${topic.keyword}`}
            >
              ×
            </button>
          </span>
        ))}
      </div>

      <form onSubmit={handleAdd} className="flex gap-2">
        <input
          type="text"
          value={keyword}
          onChange={(e) => setKeyword(e.target.value)}
          placeholder="e.g. AI, Rust, Security"
          required
          className="flex-1 rounded border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button
          type="submit"
          disabled={submitting}
          className="shrink-0 rounded bg-blue-600 px-3 py-1.5 text-sm text-white hover:bg-blue-700 disabled:opacity-50"
        >
          {submitting ? "Adding…" : "Add Topic"}
        </button>
      </form>
      {addError && (
        <p className="text-sm text-red-600 dark:text-red-400">{addError}</p>
      )}
    </div>
  );
}
