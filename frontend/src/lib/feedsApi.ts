/**
 * Feeds API module
 * Provides typed API methods for feed operations
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

export interface ApiError {
  detail: string;
  status: number;
}

export interface Feed {
  id: number;
  url: string;
  title: string;
  description: string | null;
  site_url: string | null;
  last_fetched_at: string | null;
  failure_count: number;
  user_id: number;
  created_at: string;
  updated_at: string;
}

export interface CreateFeedRequest {
  url: string;
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

export const feedsApi = {
  /**
   * Create/validate a new feed by URL
   */
  async create(data: CreateFeedRequest): Promise<Feed> {
    return request<Feed>("/api/v1/feeds", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },
};
