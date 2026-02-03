/**
 * useFeeds hook
 * Manages feed state for feeds added in-session.
 * Note: No feed listing endpoint exists, so feeds are only tracked in-session.
 */

import { useState, useCallback } from "react";
import {
  feedsApi,
  type Feed,
  type CreateFeedRequest,
  type ApiError,
} from "../lib/feedsApi";

export interface UseFeedsResult {
  feeds: Feed[];
  isLoading: boolean;
  error: string | null;
  addFeed: (data: CreateFeedRequest) => Promise<Feed>;
  clearError: () => void;
}

export function useFeeds(): UseFeedsResult {
  const [feeds, setFeeds] = useState<Feed[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const addFeed = useCallback(
    async (data: CreateFeedRequest): Promise<Feed> => {
      setIsLoading(true);
      setError(null);
      try {
        const newFeed = await feedsApi.create(data);
        setFeeds((prev) => [...prev, newFeed]);
        return newFeed;
      } catch (err) {
        const apiError = err as ApiError;
        const errorMessage = apiError.detail || "Failed to add feed";
        setError(errorMessage);
        throw err;
      } finally {
        setIsLoading(false);
      }
    },
    [],
  );

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  return {
    feeds,
    isLoading,
    error,
    addFeed,
    clearError,
  };
}
