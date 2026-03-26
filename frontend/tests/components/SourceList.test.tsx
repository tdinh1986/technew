import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { SourceList } from "@/components/SourceList";
import * as api from "@/lib/api";

vi.mock("swr", () => ({
  default: vi.fn(),
}));

import useSWR from "swr";

const mockSources = [
  { id: "1", type: "rss", url: "https://hnrss.org/frontpage", name: "Hacker News", enabled: true, last_fetched_at: null },
  { id: "2", type: "rss", url: "https://disabled.example.com/feed", name: null, enabled: false, last_fetched_at: null },
];

beforeEach(() => {
  vi.clearAllMocks();
});

describe("SourceList", () => {
  it("renders active and inactive sources", () => {
    (useSWR as ReturnType<typeof vi.fn>).mockReturnValue({
      data: { data: mockSources, error: null, meta: { total: 2 } },
      mutate: vi.fn(),
    });

    render(<SourceList />);

    expect(screen.getByText("Hacker News")).toBeInTheDocument();
    expect(screen.getByText("https://hnrss.org/frontpage")).toBeInTheDocument();
    expect(screen.getAllByRole("button", { name: /disable source|enable source/i })).toHaveLength(2);
    expect(screen.getAllByRole("button", { name: /remove source/i })).toHaveLength(2);
  });

  it("shows toggle buttons for each source", () => {
    (useSWR as ReturnType<typeof vi.fn>).mockReturnValue({
      data: { data: mockSources, error: null, meta: { total: 2 } },
      mutate: vi.fn(),
    });

    render(<SourceList />);
    expect(screen.getByText("Active")).toBeInTheDocument();
    expect(screen.getByText("Inactive")).toBeInTheDocument();
  });

  it("shows empty state when no sources", () => {
    (useSWR as ReturnType<typeof vi.fn>).mockReturnValue({
      data: { data: [], error: null, meta: { total: 0 } },
      mutate: vi.fn(),
    });

    render(<SourceList />);
    expect(screen.getByText("No sources yet.")).toBeInTheDocument();
  });

  it("displays validation error on 422 response", async () => {
    const mutate = vi.fn();
    (useSWR as ReturnType<typeof vi.fn>).mockReturnValue({
      data: { data: [], error: null, meta: { total: 0 } },
      mutate,
    });
    vi.spyOn(api, "createSource").mockResolvedValue({
      data: null,
      error: "RSS feed has no entries",
      meta: {},
    });

    render(<SourceList />);
    const input = screen.getByPlaceholderText(/https:\/\/example.com\/feed.rss/);
    fireEvent.change(input, { target: { value: "https://bad.example.com/feed" } });
    fireEvent.submit(input.closest("form")!);

    await waitFor(() => {
      expect(screen.getByText("RSS feed has no entries")).toBeInTheDocument();
    });
  });
});
