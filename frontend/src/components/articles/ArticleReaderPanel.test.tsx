import { describe, it, expect, vi } from "vitest";
import { render, screen } from "../../test/utils";
import userEvent from "@testing-library/user-event";
import { ArticleReaderPanel } from "./ArticleReaderPanel";
import type { Article } from "../../lib/articlesApi";

const mockArticle: Article = {
  id: 1,
  feed_id: 2,
  title: "Test Article Title",
  url: "https://example.com/article",
  guid: "test-guid",
  summary: "<p>This is the article body content.</p>",
  author: "Jane Smith",
  published_at: "2025-01-15T10:00:00Z",
  created_at: "2025-01-15T10:00:00Z",
};

describe("ArticleReaderPanel", () => {
  it("renders article title", () => {
    render(<ArticleReaderPanel article={mockArticle} onClose={vi.fn()} />);

    expect(screen.getByText("Test Article Title")).toBeInTheDocument();
  });

  it("renders article author", () => {
    render(<ArticleReaderPanel article={mockArticle} onClose={vi.fn()} />);

    expect(screen.getByText("Jane Smith")).toBeInTheDocument();
  });

  it("renders formatted published date", () => {
    render(<ArticleReaderPanel article={mockArticle} onClose={vi.fn()} />);

    expect(screen.getByText("January 15, 2025")).toBeInTheDocument();
  });

  it("renders 'Recently' when published_at is null", () => {
    const article = { ...mockArticle, published_at: null };
    render(<ArticleReaderPanel article={article} onClose={vi.fn()} />);

    expect(screen.getByText("Recently")).toBeInTheDocument();
  });

  it("renders article summary as HTML", () => {
    render(<ArticleReaderPanel article={mockArticle} onClose={vi.fn()} />);

    expect(
      screen.getByText("This is the article body content."),
    ).toBeInTheDocument();
  });

  it("does not render content when summary is null", () => {
    const article = { ...mockArticle, summary: null };
    render(<ArticleReaderPanel article={article} onClose={vi.fn()} />);

    expect(
      screen.queryByText("This is the article body content."),
    ).not.toBeInTheDocument();
  });

  it("renders 'Visit original article' link", () => {
    render(<ArticleReaderPanel article={mockArticle} onClose={vi.fn()} />);

    const link = screen.getByText("Visit original article");
    expect(link).toBeInTheDocument();
    expect(link.closest("a")).toHaveAttribute(
      "href",
      "https://example.com/article",
    );
    expect(link.closest("a")).toHaveAttribute("target", "_blank");
  });

  it("does not render visit link when url is null", () => {
    const article = { ...mockArticle, url: null };
    render(<ArticleReaderPanel article={article} onClose={vi.fn()} />);

    expect(
      screen.queryByText("Visit original article"),
    ).not.toBeInTheDocument();
  });

  it("renders 'Back to feed' button", () => {
    render(<ArticleReaderPanel article={mockArticle} onClose={vi.fn()} />);

    expect(screen.getByText("Back to feed")).toBeInTheDocument();
  });

  it("calls onClose when 'Back to feed' is clicked", async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();
    render(<ArticleReaderPanel article={mockArticle} onClose={onClose} />);

    await user.click(screen.getByText("Back to feed"));

    expect(onClose).toHaveBeenCalled();
  });

  it("calls onClose when Escape key is pressed", async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();
    render(<ArticleReaderPanel article={mockArticle} onClose={onClose} />);

    await user.keyboard("{Escape}");

    expect(onClose).toHaveBeenCalled();
  });

  it("renders mark-read and save buttons", () => {
    render(<ArticleReaderPanel article={mockArticle} onClose={vi.fn()} />);

    expect(
      screen.getByRole("button", { name: /mark as read/i }),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /save/i })).toBeInTheDocument();
  });

  it("calls onMarkRead when mark-read button is clicked", async () => {
    const user = userEvent.setup();
    const onMarkRead = vi.fn();
    render(
      <ArticleReaderPanel
        article={mockArticle}
        onClose={vi.fn()}
        onMarkRead={onMarkRead}
      />,
    );

    await user.click(screen.getByRole("button", { name: /mark as read/i }));

    expect(onMarkRead).toHaveBeenCalled();
  });

  it("calls onSave when save button is clicked", async () => {
    const user = userEvent.setup();
    const onSave = vi.fn();
    render(
      <ArticleReaderPanel
        article={mockArticle}
        onClose={vi.fn()}
        onSave={onSave}
      />,
    );

    await user.click(screen.getByRole("button", { name: /save/i }));

    expect(onSave).toHaveBeenCalled();
  });

  it("shows saved state for save button when isSaved", () => {
    render(
      <ArticleReaderPanel
        article={mockArticle}
        onClose={vi.fn()}
        isSaved={true}
      />,
    );

    const saveButton = screen.getByRole("button", { name: /unsave/i });
    expect(saveButton.className).toMatch(/saved/);
  });

  it("shows active state for mark-read button when isRead", () => {
    render(
      <ArticleReaderPanel
        article={mockArticle}
        onClose={vi.fn()}
        isRead={true}
      />,
    );

    const readButton = screen.getByRole("button", {
      name: /mark as unread/i,
    });
    expect(readButton.className).toMatch(/active/);
  });

  it("renders hero image placeholder", () => {
    render(<ArticleReaderPanel article={mockArticle} onClose={vi.fn()} />);

    expect(screen.getByTestId("reader-hero")).toBeInTheDocument();
  });

  it("does not render author dot separator when no author", () => {
    const article = { ...mockArticle, author: null };
    render(<ArticleReaderPanel article={article} onClose={vi.fn()} />);

    expect(screen.queryByText("Jane Smith")).not.toBeInTheDocument();
    // dot separator should not be present
    expect(screen.queryByText("·")).not.toBeInTheDocument();
  });
});
