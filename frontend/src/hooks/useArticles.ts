/**
 * useArticles hook
 * Manages article state and API operations for a collection
 */

import { useState, useCallback } from "react";
import { articlesApi, type Article, type ApiError } from "../lib/articlesApi";

export type FilterType = "all" | "unread" | "saved";

export interface UseArticlesResult {
  articles: Article[];
  total: number;
  isLoading: boolean;
  error: string | null;
  hasMore: boolean;
  filter: FilterType;
  fetchArticles: (collectionId: number, reset?: boolean) => Promise<void>;
  loadMore: (collectionId: number) => Promise<void>;
  setFilter: (filter: FilterType) => void;
  markRead: (articleId: number) => Promise<void>;
  markUnread: (articleId: number) => Promise<void>;
  saveArticle: (articleId: number) => Promise<void>;
  unsaveArticle: (articleId: number) => Promise<void>;
  clearError: () => void;
}

const PAGE_SIZE = 20;

export function useArticles(): UseArticlesResult {
  const [articles, setArticles] = useState<Article[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilterState] = useState<FilterType>("all");

  const fetchArticles = useCallback(
    async (collectionId: number, reset = true) => {
      setIsLoading(true);
      setError(null);

      const newOffset = reset ? 0 : offset;
      if (reset) {
        setArticles([]);
        setOffset(0);
      }

      try {
        const data = await articlesApi.getByCollection({
          collectionId,
          limit: PAGE_SIZE,
          offset: newOffset,
          unreadOnly: filter === "unread",
          savedOnly: filter === "saved",
        });

        if (reset) {
          setArticles(data.items);
        } else {
          setArticles((prev) => [...prev, ...data.items]);
        }
        setTotal(data.total);
        setOffset(newOffset + data.items.length);
      } catch (err) {
        const apiError = err as ApiError;
        setError(apiError.detail || "Failed to load articles");
      } finally {
        setIsLoading(false);
      }
    },
    [filter, offset],
  );

  const loadMore = useCallback(
    async (collectionId: number) => {
      if (isLoading || articles.length >= total) return;
      await fetchArticles(collectionId, false);
    },
    [fetchArticles, isLoading, articles.length, total],
  );

  const setFilter = useCallback((newFilter: FilterType) => {
    setFilterState(newFilter);
    setArticles([]);
    setOffset(0);
    setTotal(0);
  }, []);

  const markRead = useCallback(async (articleId: number) => {
    try {
      await articlesApi.markRead(articleId);
    } catch (err) {
      const apiError = err as ApiError;
      setError(apiError.detail || "Failed to mark article as read");
      throw err;
    }
  }, []);

  const markUnread = useCallback(async (articleId: number) => {
    try {
      await articlesApi.markUnread(articleId);
    } catch (err) {
      const apiError = err as ApiError;
      setError(apiError.detail || "Failed to mark article as unread");
      throw err;
    }
  }, []);

  const saveArticle = useCallback(async (articleId: number) => {
    try {
      await articlesApi.save(articleId);
    } catch (err) {
      const apiError = err as ApiError;
      setError(apiError.detail || "Failed to save article");
      throw err;
    }
  }, []);

  const unsaveArticle = useCallback(async (articleId: number) => {
    try {
      await articlesApi.unsave(articleId);
    } catch (err) {
      const apiError = err as ApiError;
      setError(apiError.detail || "Failed to unsave article");
      throw err;
    }
  }, []);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  return {
    articles,
    total,
    isLoading,
    error,
    hasMore: articles.length < total,
    filter,
    fetchArticles,
    loadMore,
    setFilter,
    markRead,
    markUnread,
    saveArticle,
    unsaveArticle,
    clearError,
  };
}
