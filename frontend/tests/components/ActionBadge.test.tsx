import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { ActionBadge } from "@/components/ActionBadge";

describe("ActionBadge", () => {
  it("renders Apply type with correct text", () => {
    render(<ActionBadge type="Apply" text="Try this tool today." />);
    expect(screen.getByText("Apply:")).toBeInTheDocument();
    expect(screen.getByText("Try this tool today.")).toBeInTheDocument();
  });

  it("renders Read More type", () => {
    render(<ActionBadge type="Read More" text="Read the full post." />);
    expect(screen.getByText("Read More:")).toBeInTheDocument();
  });

  it("applies green class for Apply type", () => {
    const { container } = render(<ActionBadge type="Apply" text="x" />);
    expect(container.firstChild).toHaveClass("bg-green-100");
  });

  it("applies blue class for Read More type", () => {
    const { container } = render(<ActionBadge type="Read More" text="x" />);
    expect(container.firstChild).toHaveClass("bg-blue-100");
  });
});
