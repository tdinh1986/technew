import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { TopicList } from "@/components/TopicList";
import * as api from "@/lib/api";

vi.mock("swr", () => ({
  default: vi.fn(),
}));

import useSWR from "swr";

const mockTopics = [
  { id: "1", keyword: "AI", active: true, created_at: "2026-03-26T00:00:00Z" },
  { id: "2", keyword: "Rust", active: true, created_at: "2026-03-26T00:00:00Z" },
];

beforeEach(() => {
  vi.clearAllMocks();
});

describe("TopicList", () => {
  it("renders keyword pills for each topic", () => {
    (useSWR as ReturnType<typeof vi.fn>).mockReturnValue({
      data: { data: mockTopics, error: null, meta: { total: 2 } },
      mutate: vi.fn(),
    });

    render(<TopicList />);
    expect(screen.getByText("AI")).toBeInTheDocument();
    expect(screen.getByText("Rust")).toBeInTheDocument();
  });

  it("renders delete buttons for each topic", () => {
    (useSWR as ReturnType<typeof vi.fn>).mockReturnValue({
      data: { data: mockTopics, error: null, meta: { total: 2 } },
      mutate: vi.fn(),
    });

    render(<TopicList />);
    expect(screen.getAllByRole("button", { name: /remove topic/i })).toHaveLength(2);
  });

  it("shows empty state when no topics", () => {
    (useSWR as ReturnType<typeof vi.fn>).mockReturnValue({
      data: { data: [], error: null, meta: { total: 0 } },
      mutate: vi.fn(),
    });

    render(<TopicList />);
    expect(screen.getByText("No topic filters yet.")).toBeInTheDocument();
  });

  it("shows 409 error on duplicate keyword submission", async () => {
    const mutate = vi.fn();
    (useSWR as ReturnType<typeof vi.fn>).mockReturnValue({
      data: { data: mockTopics, error: null, meta: { total: 2 } },
      mutate,
    });
    vi.spyOn(api, "createTopic").mockResolvedValue({
      data: null,
      error: "Topic keyword already exists",
      meta: {},
    });

    render(<TopicList />);
    const input = screen.getByPlaceholderText(/e.g. AI/);
    fireEvent.change(input, { target: { value: "AI" } });
    fireEvent.submit(input.closest("form")!);

    await waitFor(() => {
      expect(screen.getByText("Topic keyword already exists")).toBeInTheDocument();
    });
  });
});
