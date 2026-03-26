import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { DigestReport } from "@/components/DigestReport";
import type { DigestReport as DigestReportType } from "@/lib/types";

const fixture: DigestReportType = {
  id: "report-1",
  created_at: "2026-03-24T06:00:00Z",
  article_count: 2,
  topic_sections: [
    {
      topic: "AI & Machine Learning",
      article_count: 2,
      actionable_insight: { type: "Apply", text: "Try the new API." },
      articles: [
        { id: "a1", title: "GPT-5 Released", source: "TechCrunch", url: "https://tc.com", bullets: ["Faster.", "Cheaper."] },
        { id: "a2", title: "Claude Update", source: "Ars", url: "https://ars.com", bullets: ["Better reasoning."] },
      ],
    },
  ],
};

describe("DigestReport", () => {
  it("renders the digest header", () => {
    render(<DigestReport report={fixture} />);
    expect(screen.getByText("Tech Digest")).toBeInTheDocument();
    expect(screen.getByText(/2 articles/)).toBeInTheDocument();
  });

  it("renders all topic sections", () => {
    render(<DigestReport report={fixture} />);
    expect(screen.getByText("AI & Machine Learning")).toBeInTheDocument();
  });

  it("renders article titles", () => {
    render(<DigestReport report={fixture} />);
    expect(screen.getByText("GPT-5 Released")).toBeInTheDocument();
    expect(screen.getByText("Claude Update")).toBeInTheDocument();
  });

  it("renders actionable insight", () => {
    render(<DigestReport report={fixture} />);
    expect(screen.getByText("Try the new API.")).toBeInTheDocument();
  });
});
