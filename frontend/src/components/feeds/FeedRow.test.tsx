import { describe, it, expect, vi } from "vitest";
import { render, screen } from "../../test/utils";
import userEvent from "@testing-library/user-event";
import { FeedRow } from "./FeedRow";
import type { Feed } from "../../lib/feedsApi";

const mockFeed: Feed = {
  id: 1,
  url: "https://example.com/rss",
  title: "Example Feed",
  description: "A test feed",
  site_url: "https://example.com",
  last_fetched_at: new Date().toISOString(),
  failure_count: 0,
  user_id: 1,
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
};

describe("FeedRow", () => {
  it("renders feed title", () => {
    render(<FeedRow feed={mockFeed} onAssign={vi.fn()} />);

    expect(screen.getByText("Example Feed")).toBeInTheDocument();
  });

  it("renders 'Untitled Feed' when title is empty", () => {
    const untitledFeed = { ...mockFeed, title: "" };
    render(<FeedRow feed={untitledFeed} onAssign={vi.fn()} />);

    expect(screen.getByText("Untitled Feed")).toBeInTheDocument();
  });

  it("renders truncated URL", () => {
    render(<FeedRow feed={mockFeed} onAssign={vi.fn()} />);

    expect(screen.getByText("example.com/rss")).toBeInTheDocument();
  });

  it("truncates long URLs", () => {
    const longUrlFeed = {
      ...mockFeed,
      url: "https://example.com/very/long/path/that/exceeds/the/limit/for/display",
    };
    render(<FeedRow feed={longUrlFeed} onAssign={vi.fn()} />);

    const urlText = screen.getByText(/example\.com/);
    expect(urlText.textContent).toContain("...");
  });

  it("shows 'Active' badge when feed has no failures", () => {
    render(<FeedRow feed={mockFeed} onAssign={vi.fn()} />);

    expect(screen.getByText("Active")).toBeInTheDocument();
  });

  it("shows 'Failed' badge when feed has failures", () => {
    const failedFeed = { ...mockFeed, failure_count: 3 };
    render(<FeedRow feed={failedFeed} onAssign={vi.fn()} />);

    expect(screen.getAllByText("Failed")).toHaveLength(2); // Badge and last fetched
  });

  it("shows 'Never' when last_fetched_at is null", () => {
    const neverFetchedFeed = { ...mockFeed, last_fetched_at: null };
    render(<FeedRow feed={neverFetchedFeed} onAssign={vi.fn()} />);

    expect(screen.getByText("Never")).toBeInTheDocument();
  });

  it("calls onAssign when assign button is clicked", async () => {
    const user = userEvent.setup();
    const onAssign = vi.fn();
    render(<FeedRow feed={mockFeed} onAssign={onAssign} />);

    const assignButton = screen.getByRole("button", {
      name: /assign example feed to collection/i,
    });
    await user.click(assignButton);

    expect(onAssign).toHaveBeenCalledWith(mockFeed);
  });

  it("renders delete button when onDelete is provided", async () => {
    const user = userEvent.setup();
    const onDelete = vi.fn();
    render(<FeedRow feed={mockFeed} onAssign={vi.fn()} onDelete={onDelete} />);

    const deleteButton = screen.getByRole("button", {
      name: /delete example feed/i,
    });
    await user.click(deleteButton);

    expect(onDelete).toHaveBeenCalledWith(mockFeed);
  });

  it("does not render delete button when onDelete is not provided", () => {
    render(<FeedRow feed={mockFeed} onAssign={vi.fn()} />);

    expect(
      screen.queryByRole("button", { name: /delete/i }),
    ).not.toBeInTheDocument();
  });

  it("formats time ago correctly for recent fetch", () => {
    const recentFeed = {
      ...mockFeed,
      last_fetched_at: new Date(Date.now() - 5 * 60000).toISOString(), // 5 mins ago
    };
    render(<FeedRow feed={recentFeed} onAssign={vi.fn()} />);

    expect(screen.getByText("5 min ago")).toBeInTheDocument();
  });

  it("formats time ago correctly for hours", () => {
    const hoursFeed = {
      ...mockFeed,
      last_fetched_at: new Date(Date.now() - 2 * 3600000).toISOString(), // 2 hours ago
    };
    render(<FeedRow feed={hoursFeed} onAssign={vi.fn()} />);

    expect(screen.getByText("2 hours ago")).toBeInTheDocument();
  });
});
