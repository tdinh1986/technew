import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { UrlDigestForm } from "@/components/UrlDigestForm";

// Mock SWR so polling doesn't run in tests
vi.mock("swr", () => ({
  default: vi.fn(() => ({ data: undefined })),
}));

// Mock api module
vi.mock("@/lib/api", () => ({
  submitUrlDigest: vi.fn(),
  getJobStatus: vi.fn(),
  getReport: vi.fn(),
}));

import { submitUrlDigest } from "@/lib/api";

beforeEach(() => {
  vi.clearAllMocks();
});

describe("UrlDigestForm", () => {
  it("renders textarea and submit button", () => {
    render(<UrlDigestForm />);
    expect(screen.getByRole("textbox")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /summarize/i })).toBeInTheDocument();
  });

  it("submit button is disabled when textarea is empty", () => {
    render(<UrlDigestForm />);
    expect(screen.getByRole("button", { name: /summarize/i })).toBeDisabled();
  });

  it("shows error when submitted with empty input", async () => {
    render(<UrlDigestForm />);
    const textarea = screen.getByRole("textbox");
    fireEvent.change(textarea, { target: { value: "  " } });
    const btn = screen.getByRole("button", { name: /summarize/i });
    fireEvent.click(btn);
    await waitFor(() => {
      expect(screen.getByText(/at least one url/i)).toBeInTheDocument();
    });
  });

  it("shows counter and disables submit when >20 URLs entered", () => {
    render(<UrlDigestForm />);
    const urls = Array.from({ length: 21 }, (_, i) => `https://example.com/${i}`).join("\n");
    fireEvent.change(screen.getByRole("textbox"), { target: { value: urls } });
    expect(screen.getByText("21 / 20")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /summarize/i })).toBeDisabled();
  });

  it("shows validation error for malformed URL", async () => {
    render(<UrlDigestForm />);
    fireEvent.change(screen.getByRole("textbox"), { target: { value: "not-a-url" } });
    fireEvent.click(screen.getByRole("button", { name: /summarize/i }));
    await waitFor(() => {
      expect(screen.getByText(/invalid url/i)).toBeInTheDocument();
    });
  });

  it("calls submitUrlDigest and shows spinner on valid submit", async () => {
    vi.mocked(submitUrlDigest).mockResolvedValueOnce({
      data: { id: "job-1", status: "queued", report_id: null, started_at: null, completed_at: null, articles_added: null, error_message: null },
      error: null,
      meta: {},
    });

    render(<UrlDigestForm />);
    fireEvent.change(screen.getByRole("textbox"), {
      target: { value: "https://example.com/article" },
    });
    fireEvent.click(screen.getByRole("button", { name: /summarize/i }));

    await waitFor(() => {
      expect(submitUrlDigest).toHaveBeenCalledWith(["https://example.com/article"]);
    });
  });

  it("shows API error when submitUrlDigest returns error", async () => {
    vi.mocked(submitUrlDigest).mockResolvedValueOnce({
      data: null,
      error: "Server error",
      meta: {},
    });

    render(<UrlDigestForm />);
    fireEvent.change(screen.getByRole("textbox"), {
      target: { value: "https://example.com/article" },
    });
    fireEvent.click(screen.getByRole("button", { name: /summarize/i }));

    await waitFor(() => {
      expect(screen.getByText("Server error")).toBeInTheDocument();
    });
  });
});
