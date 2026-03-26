import type { DigestReport as DigestReportType } from "@/lib/types";
import { TopicSection } from "./TopicSection";

interface Props {
  report: DigestReportType;
}

export function DigestReport({ report }: Props) {
  const date = new Date(report.created_at).toLocaleDateString("en-US", {
    weekday: "long",
    year: "numeric",
    month: "long",
    day: "numeric",
  });

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      <header className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">Tech Digest</h1>
        <p className="text-gray-500 dark:text-gray-400 mt-1">
          {date} · {report.article_count} articles
        </p>
      </header>
      {report.topic_sections.map((section) => (
        <TopicSection
          key={section.topic}
          topic={section.topic}
          articles={section.articles}
          actionable_insight={section.actionable_insight}
        />
      ))}
    </div>
  );
}
