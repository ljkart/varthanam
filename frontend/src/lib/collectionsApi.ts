/**
 * Collections API module
 * Provides typed API methods for collection CRUD operations
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

export interface ApiError {
  detail: string;
  status: number;
}

export interface Collection {
  id: number;
  name: string;
  description: string | null;
  user_id: number;
  created_at: string;
  updated_at: string;
}

export interface CreateCollectionRequest {
  name: string;
  description?: string;
}

export interface UpdateCollectionRequest {
  name?: string;
  description?: string;
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

export const collectionsApi = {
  /**
   * Fetch all collections for the current user
   */
  async getAll(): Promise<Collection[]> {
    return request<Collection[]>("/api/v1/collections");
  },

  /**
   * Fetch a single collection by ID
   */
  async getById(id: number): Promise<Collection> {
    return request<Collection>(`/api/v1/collections/${id}`);
  },

  /**
   * Create a new collection
   */
  async create(data: CreateCollectionRequest): Promise<Collection> {
    return request<Collection>("/api/v1/collections", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  /**
   * Update an existing collection
   */
  async update(id: number, data: UpdateCollectionRequest): Promise<Collection> {
    return request<Collection>(`/api/v1/collections/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  },

  /**
   * Delete a collection
   */
  async delete(id: number): Promise<void> {
    return request<void>(`/api/v1/collections/${id}`, {
      method: "DELETE",
    });
  },
};
