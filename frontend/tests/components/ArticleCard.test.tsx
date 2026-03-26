import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { ArticleCard } from "@/components/ArticleCard";

describe("ArticleCard", () => {
  const props = {
    title: "New AI Model Released",
    source: "TechCrunch",
    url: "https://techcrunch.com/article",
    bullets: ["Point one.", "Point two.", "Point three."],
  };

  it("renders title as a link with correct href", () => {
    render(<ArticleCard {...props} />);
    const link = screen.getByRole("link", { name: props.title });
    expect(link).toHaveAttribute("href", props.url);
    expect(link).toHaveAttribute("target", "_blank");
  });

  it("renders source label", () => {
    render(<ArticleCard {...props} />);
    expect(screen.getByText("TechCrunch")).toBeInTheDocument();
  });

  it("renders all bullet points", () => {
    render(<ArticleCard {...props} />);
    props.bullets.forEach((b) => expect(screen.getByText(b)).toBeInTheDocument());
  });
});
