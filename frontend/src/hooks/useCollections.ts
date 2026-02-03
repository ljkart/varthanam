/**
 * useCollections hook
 * Manages collection state and API operations
 */

import { useState, useEffect, useCallback } from "react";
import {
  collectionsApi,
  type Collection,
  type CreateCollectionRequest,
  type UpdateCollectionRequest,
  type ApiError,
} from "../lib/collectionsApi";

export interface UseCollectionsResult {
  collections: Collection[];
  isLoading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
  createCollection: (data: CreateCollectionRequest) => Promise<Collection>;
  updateCollection: (
    id: number,
    data: UpdateCollectionRequest,
  ) => Promise<Collection>;
  deleteCollection: (id: number) => Promise<void>;
}

export function useCollections(): UseCollectionsResult {
  const [collections, setCollections] = useState<Collection[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchCollections = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await collectionsApi.getAll();
      setCollections(data);
    } catch (err) {
      const apiError = err as ApiError;
      setError(apiError.detail || "Failed to load collections");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchCollections();
  }, [fetchCollections]);

  const createCollection = useCallback(
    async (data: CreateCollectionRequest): Promise<Collection> => {
      const newCollection = await collectionsApi.create(data);
      setCollections((prev) => [...prev, newCollection]);
      return newCollection;
    },
    [],
  );

  const updateCollection = useCallback(
    async (id: number, data: UpdateCollectionRequest): Promise<Collection> => {
      const updated = await collectionsApi.update(id, data);
      setCollections((prev) => prev.map((c) => (c.id === id ? updated : c)));
      return updated;
    },
    [],
  );

  const deleteCollection = useCallback(async (id: number): Promise<void> => {
    await collectionsApi.delete(id);
    setCollections((prev) => prev.filter((c) => c.id !== id));
  }, []);

  return {
    collections,
    isLoading,
    error,
    refetch: fetchCollections,
    createCollection,
    updateCollection,
    deleteCollection,
  };
}
