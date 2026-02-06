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

  it("defaults to stacked variant", () => {
    const { container } = render(<ArticleCard article={mockArticle} />);

    expect((container.firstChild as HTMLElement)?.className).toMatch(/stacked/);
  });

  it("renders article summary in stacked variant", () => {
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

    expect(screen.getByText(/ago|Just now/i)).toBeInTheDocument();
  });

  it("calls onClick when card is clicked", async () => {
    const user = userEvent.setup();
    const onClick = vi.fn();
    render(<ArticleCard article={mockArticle} onClick={onClick} />);

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

  it("calls onSave when save button is clicked in stacked variant", async () => {
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

    expect((container.firstChild as HTMLElement)?.className).toMatch(/read/);
  });

  it("shows active state for save button when isSaved is true", () => {
    render(<ArticleCard article={mockArticle} isSaved={true} />);

    const saveButton = screen.getByRole("button", { name: /unsave/i });
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

  // ── Stacked variant ──

  it("shows thumbnail in stacked variant", () => {
    render(<ArticleCard article={mockArticle} variant="stacked" />);

    expect(screen.getByTestId("article-thumbnail")).toBeInTheDocument();
  });

  it("does not show full image in stacked variant", () => {
    render(<ArticleCard article={mockArticle} variant="stacked" />);

    expect(screen.queryByTestId("article-image")).not.toBeInTheDocument();
  });

  it("shows mark-read and save action buttons in stacked variant", () => {
    render(<ArticleCard article={mockArticle} variant="stacked" />);

    expect(
      screen.getByRole("button", { name: /mark as read/i }),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /save/i })).toBeInTheDocument();
  });

  // ── Grid variant ──

  it("applies grid class when variant is grid", () => {
    const { container } = render(
      <ArticleCard article={mockArticle} variant="grid" />,
    );

    expect((container.firstChild as HTMLElement)?.className).toMatch(/grid/);
  });

  it("shows full image in grid variant", () => {
    render(<ArticleCard article={mockArticle} variant="grid" />);

    expect(screen.getByTestId("article-image")).toBeInTheDocument();
  });

  it("does not show thumbnail in grid variant", () => {
    render(<ArticleCard article={mockArticle} variant="grid" />);

    expect(screen.queryByTestId("article-thumbnail")).not.toBeInTheDocument();
  });

  it("does not show summary in grid variant", () => {
    render(<ArticleCard article={mockArticle} variant="grid" />);

    expect(
      screen.queryByText(/This is a test article summary/),
    ).not.toBeInTheDocument();
  });

  it("shows save button in grid variant corner", () => {
    render(<ArticleCard article={mockArticle} variant="grid" />);

    expect(screen.getByRole("button", { name: /save/i })).toBeInTheDocument();
  });

  it("does not show mark-read button in grid variant", () => {
    render(<ArticleCard article={mockArticle} variant="grid" />);

    expect(
      screen.queryByRole("button", { name: /mark as read/i }),
    ).not.toBeInTheDocument();
  });

  it("shows placeholder initials from title", () => {
    render(<ArticleCard article={mockArticle} variant="stacked" />);

    // "Test Article Title" → "TA"
    expect(screen.getByText("TA")).toBeInTheDocument();
  });

  it("calls onSave from grid variant corner button", async () => {
    const user = userEvent.setup();
    const onSave = vi.fn();
    render(
      <ArticleCard article={mockArticle} variant="grid" onSave={onSave} />,
    );

    const saveButton = screen.getByRole("button", { name: /save/i });
    await user.click(saveButton);

    expect(onSave).toHaveBeenCalled();
  });
});
