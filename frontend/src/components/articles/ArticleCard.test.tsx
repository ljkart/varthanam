import { describe, it, expect, vi } from "vitest";
import { render, screen } from "../../test/utils";
import userEvent from "@testing-library/user-event";
import { ArticleCard } from "./ArticleCard";
import type { Article } from "../../lib/articlesApi";

const mockArticle: Article = {
  id: 1,
  feed_id: 1,
  title: "Test Article Title",
  url: "https://example.com/article",
  guid: "test-guid",
  summary: "This is a test article summary for testing purposes.",
  author: "John Doe",
  published_at: new Date().toISOString(),
  created_at: new Date().toISOString(),
};

describe("ArticleCard", () => {
  it("renders article title", () => {
    render(<ArticleCard article={mockArticle} />);

    expect(screen.getByText("Test Article Title")).toBeInTheDocument();
  });

  it("renders article summary", () => {
    render(<ArticleCard article={mockArticle} />);

    expect(
      screen.getByText(/This is a test article summary/),
    ).toBeInTheDocument();
  });

  it("renders author name", () => {
    render(<ArticleCard article={mockArticle} />);

    expect(screen.getByText("John Doe")).toBeInTheDocument();
  });

  it("renders time ago", () => {
    render(<ArticleCard article={mockArticle} />);

    // Should show some time indicator
    expect(screen.getByText(/ago|Just now/i)).toBeInTheDocument();
  });

  it("calls onClick when card is clicked", async () => {
    const user = userEvent.setup();
    const onClick = vi.fn();
    render(<ArticleCard article={mockArticle} onClick={onClick} />);

    // Click on the article title to trigger the card's onClick
    await user.click(screen.getByText("Test Article Title"));

    expect(onClick).toHaveBeenCalled();
  });

  it("calls onMarkRead when mark read button is clicked", async () => {
    const user = userEvent.setup();
    const onMarkRead = vi.fn();
    render(<ArticleCard article={mockArticle} onMarkRead={onMarkRead} />);

    const markReadButton = screen.getByRole("button", {
      name: /mark as read/i,
    });
    await user.click(markReadButton);

    expect(onMarkRead).toHaveBeenCalled();
  });

  it("calls onSave when save button is clicked", async () => {
    const user = userEvent.setup();
    const onSave = vi.fn();
    render(<ArticleCard article={mockArticle} onSave={onSave} />);

    const saveButton = screen.getByRole("button", { name: /save/i });
    await user.click(saveButton);

    expect(onSave).toHaveBeenCalled();
  });

  it("applies read style when isRead is true", () => {
    const { container } = render(
      <ArticleCard article={mockArticle} isRead={true} />,
    );

    // CSS modules add prefixes, so check for partial class name
    expect((container.firstChild as HTMLElement)?.className).toMatch(/read/);
  });

  it("shows active state for save button when isSaved is true", () => {
    render(<ArticleCard article={mockArticle} isSaved={true} />);

    const saveButton = screen.getByRole("button", { name: /unsave/i });
    // CSS modules add prefixes, so check for partial class name
    expect(saveButton.className).toMatch(/saved/);
  });

  it("does not render summary when article has no summary", () => {
    const articleWithoutSummary = { ...mockArticle, summary: null };
    render(<ArticleCard article={articleWithoutSummary} />);

    expect(
      screen.queryByText(/This is a test article summary/),
    ).not.toBeInTheDocument();
  });

  it("does not render author when article has no author", () => {
    const articleWithoutAuthor = { ...mockArticle, author: null };
    render(<ArticleCard article={articleWithoutAuthor} />);

    expect(screen.queryByText("John Doe")).not.toBeInTheDocument();
  });

  it("shows 'Recently' when published_at is null", () => {
    const articleWithoutDate = { ...mockArticle, published_at: null };
    render(<ArticleCard article={articleWithoutDate} />);

    expect(screen.getByText("Recently")).toBeInTheDocument();
  });

  it("does not propagate click when action buttons are clicked", async () => {
    const user = userEvent.setup();
    const onClick = vi.fn();
    const onSave = vi.fn();
    render(
      <ArticleCard article={mockArticle} onClick={onClick} onSave={onSave} />,
    );

    const saveButton = screen.getByRole("button", { name: /save/i });
    await user.click(saveButton);

    expect(onSave).toHaveBeenCalled();
    expect(onClick).not.toHaveBeenCalled();
  });
});
