import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useArticles } from "./useArticles";
import { articlesApi } from "../lib/articlesApi";
import type { Article, PaginatedArticles } from "../lib/articlesApi";

// Mock the articlesApi
vi.mock("../lib/articlesApi", () => ({
  articlesApi: {
    getByCollection: vi.fn(),
    markRead: vi.fn(),
    markUnread: vi.fn(),
    save: vi.fn(),
    unsave: vi.fn(),
  },
}));

const mockArticle: Article = {
  id: 1,
  feed_id: 1,
  title: "Test Article",
  url: "https://example.com",
  guid: "test-guid",
  summary: "Test summary",
  author: "Test Author",
  published_at: new Date().toISOString(),
  created_at: new Date().toISOString(),
};

const mockPaginatedResponse: PaginatedArticles = {
  items: [mockArticle],
  total: 1,
  limit: 20,
  offset: 0,
};

describe("useArticles", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("initializes with empty articles array", () => {
    const { result } = renderHook(() => useArticles());

    expect(result.current.articles).toEqual([]);
    expect(result.current.total).toBe(0);
    expect(result.current.isLoading).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it("fetches articles for a collection", async () => {
    vi.mocked(articlesApi.getByCollection).mockResolvedValue(
      mockPaginatedResponse,
    );

    const { result } = renderHook(() => useArticles());

    await act(async () => {
      await result.current.fetchArticles(1);
    });

    expect(articlesApi.getByCollection).toHaveBeenCalledWith({
      collectionId: 1,
      limit: 20,
      offset: 0,
      unreadOnly: false,
      savedOnly: false,
    });
    expect(result.current.articles).toHaveLength(1);
    expect(result.current.total).toBe(1);
  });

  it("sets loading state during fetch", async () => {
    let resolvePromise: (value: PaginatedArticles) => void;
    vi.mocked(articlesApi.getByCollection).mockReturnValue(
      new Promise((resolve) => {
        resolvePromise = resolve;
      }),
    );

    const { result } = renderHook(() => useArticles());

    let fetchPromise: Promise<void>;
    act(() => {
      fetchPromise = result.current.fetchArticles(1);
    });

    expect(result.current.isLoading).toBe(true);

    await act(async () => {
      resolvePromise!(mockPaginatedResponse);
      await fetchPromise;
    });

    expect(result.current.isLoading).toBe(false);
  });

  it("handles fetch errors", async () => {
    vi.mocked(articlesApi.getByCollection).mockRejectedValue({
      detail: "Failed to load",
      status: 500,
    });

    const { result } = renderHook(() => useArticles());

    await act(async () => {
      await result.current.fetchArticles(1);
    });

    expect(result.current.error).toBe("Failed to load");
    expect(result.current.articles).toHaveLength(0);
  });

  it("marks article as read", async () => {
    vi.mocked(articlesApi.markRead).mockResolvedValue({
      article_id: 1,
      is_read: true,
      is_saved: false,
      read_at: new Date().toISOString(),
      saved_at: null,
    });

    const { result } = renderHook(() => useArticles());

    await act(async () => {
      await result.current.markRead(1);
    });

    expect(articlesApi.markRead).toHaveBeenCalledWith(1);
  });

  it("marks article as unread", async () => {
    vi.mocked(articlesApi.markUnread).mockResolvedValue({
      article_id: 1,
      is_read: false,
      is_saved: false,
      read_at: null,
      saved_at: null,
    });

    const { result } = renderHook(() => useArticles());

    await act(async () => {
      await result.current.markUnread(1);
    });

    expect(articlesApi.markUnread).toHaveBeenCalledWith(1);
  });

  it("saves article", async () => {
    vi.mocked(articlesApi.save).mockResolvedValue({
      article_id: 1,
      is_read: false,
      is_saved: true,
      read_at: null,
      saved_at: new Date().toISOString(),
    });

    const { result } = renderHook(() => useArticles());

    await act(async () => {
      await result.current.saveArticle(1);
    });

    expect(articlesApi.save).toHaveBeenCalledWith(1);
  });

  it("unsaves article", async () => {
    vi.mocked(articlesApi.unsave).mockResolvedValue({
      article_id: 1,
      is_read: false,
      is_saved: false,
      read_at: null,
      saved_at: null,
    });

    const { result } = renderHook(() => useArticles());

    await act(async () => {
      await result.current.unsaveArticle(1);
    });

    expect(articlesApi.unsave).toHaveBeenCalledWith(1);
  });

  it("changes filter and resets articles", () => {
    const { result } = renderHook(() => useArticles());

    act(() => {
      result.current.setFilter("unread");
    });

    expect(result.current.filter).toBe("unread");
    expect(result.current.articles).toEqual([]);
  });

  it("fetches with unread filter", async () => {
    vi.mocked(articlesApi.getByCollection).mockResolvedValue(
      mockPaginatedResponse,
    );

    const { result } = renderHook(() => useArticles());

    act(() => {
      result.current.setFilter("unread");
    });

    await act(async () => {
      await result.current.fetchArticles(1);
    });

    expect(articlesApi.getByCollection).toHaveBeenCalledWith(
      expect.objectContaining({
        unreadOnly: true,
        savedOnly: false,
      }),
    );
  });

  it("fetches with saved filter", async () => {
    vi.mocked(articlesApi.getByCollection).mockResolvedValue(
      mockPaginatedResponse,
    );

    const { result } = renderHook(() => useArticles());

    act(() => {
      result.current.setFilter("saved");
    });

    await act(async () => {
      await result.current.fetchArticles(1);
    });

    expect(articlesApi.getByCollection).toHaveBeenCalledWith(
      expect.objectContaining({
        unreadOnly: false,
        savedOnly: true,
      }),
    );
  });

  it("clears error", async () => {
    vi.mocked(articlesApi.getByCollection).mockRejectedValue({
      detail: "Error",
    });

    const { result } = renderHook(() => useArticles());

    await act(async () => {
      await result.current.fetchArticles(1);
    });

    expect(result.current.error).toBe("Error");

    act(() => {
      result.current.clearError();
    });

    expect(result.current.error).toBeNull();
  });

  it("computes hasMore correctly", async () => {
    vi.mocked(articlesApi.getByCollection).mockResolvedValue({
      items: [mockArticle],
      total: 50,
      limit: 20,
      offset: 0,
    });

    const { result } = renderHook(() => useArticles());

    await act(async () => {
      await result.current.fetchArticles(1);
    });

    expect(result.current.hasMore).toBe(true);
  });
});
