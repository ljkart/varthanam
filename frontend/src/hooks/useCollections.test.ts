import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor, act } from "@testing-library/react";
import { useCollections } from "./useCollections";

// Mock the collectionsApi module
vi.mock("../lib/collectionsApi", () => ({
  collectionsApi: {
    getAll: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
  },
}));

import { collectionsApi } from "../lib/collectionsApi";

const mockCollections = [
  {
    id: 1,
    name: "Tech News",
    description: "Technology articles",
    user_id: 1,
    created_at: "2024-01-01T00:00:00Z",
    updated_at: "2024-01-01T00:00:00Z",
  },
  {
    id: 2,
    name: "AI & ML",
    description: null,
    user_id: 1,
    created_at: "2024-01-02T00:00:00Z",
    updated_at: "2024-01-02T00:00:00Z",
  },
];

describe("useCollections", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("fetches collections on mount", async () => {
    vi.mocked(collectionsApi.getAll).mockResolvedValueOnce(mockCollections);

    const { result } = renderHook(() => useCollections());

    expect(result.current.isLoading).toBe(true);

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.collections).toEqual(mockCollections);
    expect(result.current.error).toBeNull();
  });

  it("handles fetch error", async () => {
    vi.mocked(collectionsApi.getAll).mockRejectedValueOnce({
      detail: "Failed to fetch",
      status: 500,
    });

    const { result } = renderHook(() => useCollections());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.error).toBe("Failed to fetch");
    expect(result.current.collections).toEqual([]);
  });

  it("creates a collection and adds to list", async () => {
    vi.mocked(collectionsApi.getAll).mockResolvedValueOnce([]);
    const newCollection = {
      id: 3,
      name: "New Collection",
      description: "Description",
      user_id: 1,
      created_at: "2024-01-03T00:00:00Z",
      updated_at: "2024-01-03T00:00:00Z",
    };
    vi.mocked(collectionsApi.create).mockResolvedValueOnce(newCollection);

    const { result } = renderHook(() => useCollections());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    await act(async () => {
      await result.current.createCollection({
        name: "New Collection",
        description: "Description",
      });
    });

    expect(result.current.collections).toContainEqual(newCollection);
  });

  it("updates a collection in the list", async () => {
    vi.mocked(collectionsApi.getAll).mockResolvedValueOnce(mockCollections);
    const updatedCollection = {
      ...mockCollections[0],
      name: "Updated Name",
    };
    vi.mocked(collectionsApi.update).mockResolvedValueOnce(updatedCollection);

    const { result } = renderHook(() => useCollections());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    await act(async () => {
      await result.current.updateCollection(1, { name: "Updated Name" });
    });

    expect(result.current.collections[0].name).toBe("Updated Name");
  });

  it("deletes a collection from the list", async () => {
    vi.mocked(collectionsApi.getAll).mockResolvedValueOnce(mockCollections);
    vi.mocked(collectionsApi.delete).mockResolvedValueOnce(undefined);

    const { result } = renderHook(() => useCollections());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.collections).toHaveLength(2);

    await act(async () => {
      await result.current.deleteCollection(1);
    });

    expect(result.current.collections).toHaveLength(1);
    expect(result.current.collections[0].id).toBe(2);
  });

  it("refetches collections", async () => {
    vi.mocked(collectionsApi.getAll)
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce(mockCollections);

    const { result } = renderHook(() => useCollections());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.collections).toEqual([]);

    await act(async () => {
      await result.current.refetch();
    });

    expect(result.current.collections).toEqual(mockCollections);
  });
});
