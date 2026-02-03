import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useFeeds } from "./useFeeds";
import { feedsApi } from "../lib/feedsApi";
import type { Feed } from "../lib/feedsApi";

// Mock the feedsApi
vi.mock("../lib/feedsApi", () => ({
  feedsApi: {
    create: vi.fn(),
  },
}));

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

describe("useFeeds", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("initializes with empty feeds array", () => {
    const { result } = renderHook(() => useFeeds());

    expect(result.current.feeds).toEqual([]);
    expect(result.current.isLoading).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it("adds a feed successfully", async () => {
    vi.mocked(feedsApi.create).mockResolvedValue(mockFeed);

    const { result } = renderHook(() => useFeeds());

    await act(async () => {
      const feed = await result.current.addFeed({
        url: "https://example.com/rss",
      });
      expect(feed).toEqual(mockFeed);
    });

    expect(result.current.feeds).toHaveLength(1);
    expect(result.current.feeds[0]).toEqual(mockFeed);
    expect(result.current.error).toBeNull();
  });

  it("sets loading state during addFeed", async () => {
    let resolvePromise: (value: Feed) => void;
    vi.mocked(feedsApi.create).mockReturnValue(
      new Promise((resolve) => {
        resolvePromise = resolve;
      }),
    );

    const { result } = renderHook(() => useFeeds());

    let addFeedPromise: Promise<Feed>;
    act(() => {
      addFeedPromise = result.current.addFeed({
        url: "https://example.com/rss",
      });
    });

    expect(result.current.isLoading).toBe(true);

    await act(async () => {
      resolvePromise!(mockFeed);
      await addFeedPromise;
    });

    expect(result.current.isLoading).toBe(false);
  });

  it("handles API errors", async () => {
    vi.mocked(feedsApi.create).mockRejectedValue({
      detail: "Invalid feed URL",
      status: 400,
    });

    const { result } = renderHook(() => useFeeds());

    await act(async () => {
      try {
        await result.current.addFeed({ url: "invalid-url" });
      } catch {
        // Expected to throw
      }
    });

    expect(result.current.error).toBe("Invalid feed URL");
    expect(result.current.feeds).toHaveLength(0);
  });

  it("clears error", async () => {
    vi.mocked(feedsApi.create).mockRejectedValue({
      detail: "Error occurred",
      status: 500,
    });

    const { result } = renderHook(() => useFeeds());

    await act(async () => {
      try {
        await result.current.addFeed({ url: "https://example.com" });
      } catch {
        // Expected to throw
      }
    });

    expect(result.current.error).toBe("Error occurred");

    act(() => {
      result.current.clearError();
    });

    expect(result.current.error).toBeNull();
  });

  it("accumulates multiple feeds", async () => {
    const feed1 = { ...mockFeed, id: 1, title: "Feed 1" };
    const feed2 = { ...mockFeed, id: 2, title: "Feed 2" };

    vi.mocked(feedsApi.create)
      .mockResolvedValueOnce(feed1)
      .mockResolvedValueOnce(feed2);

    const { result } = renderHook(() => useFeeds());

    await act(async () => {
      await result.current.addFeed({ url: "https://example.com/feed1" });
    });

    await act(async () => {
      await result.current.addFeed({ url: "https://example.com/feed2" });
    });

    expect(result.current.feeds).toHaveLength(2);
    expect(result.current.feeds[0]).toEqual(feed1);
    expect(result.current.feeds[1]).toEqual(feed2);
  });

  it("clears previous error on new addFeed attempt", async () => {
    vi.mocked(feedsApi.create)
      .mockRejectedValueOnce({ detail: "First error" })
      .mockResolvedValueOnce(mockFeed);

    const { result } = renderHook(() => useFeeds());

    await act(async () => {
      try {
        await result.current.addFeed({ url: "https://example.com" });
      } catch {
        // Expected
      }
    });

    expect(result.current.error).toBe("First error");

    await act(async () => {
      await result.current.addFeed({ url: "https://example.com" });
    });

    expect(result.current.error).toBeNull();
  });

  it("uses fallback error message when detail is missing", async () => {
    vi.mocked(feedsApi.create).mockRejectedValue({});

    const { result } = renderHook(() => useFeeds());

    await act(async () => {
      try {
        await result.current.addFeed({ url: "https://example.com" });
      } catch {
        // Expected
      }
    });

    expect(result.current.error).toBe("Failed to add feed");
  });
});
