/**
 * Collection Feeds API module
 * Provides typed API methods for assigning/unassigning feeds to collections
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

export interface ApiError {
  detail: string;
  status: number;
}

export interface CollectionFeed {
  collection_id: number;
  feed_id: number;
  created_at: string;
}

export interface AssignFeedRequest {
  feed_id: number;
}

async function request<T>(
  endpoint: string,
  options: RequestInit = {},
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  const token = localStorage.getItem("access_token");

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  if (options.headers) {
    Object.assign(headers, options.headers as Record<string, string>);
  }

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({
      detail: "An unexpected error occurred",
    }));
    throw {
      detail: error.detail || "An unexpected error occurred",
      status: response.status,
    } as ApiError;
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return undefined as T;
  }

  return response.json();
}

export const collectionFeedsApi = {
  /**
   * Assign a feed to a collection
   */
  async assign(collectionId: number, feedId: number): Promise<CollectionFeed> {
    return request<CollectionFeed>(
      `/api/v1/collections/${collectionId}/feeds`,
      {
        method: "POST",
        body: JSON.stringify({ feed_id: feedId }),
      },
    );
  },

  /**
   * Unassign a feed from a collection
   */
  async unassign(collectionId: number, feedId: number): Promise<void> {
    return request<void>(
      `/api/v1/collections/${collectionId}/feeds/${feedId}`,
      {
        method: "DELETE",
      },
    );
  },
};
