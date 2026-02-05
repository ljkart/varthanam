/**
 * Articles API module
 * Provides typed API methods for article operations
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

export interface ApiError {
  detail: string;
  status: number;
}

export interface Article {
  id: number;
  feed_id: number;
  title: string;
  url: string | null;
  guid: string | null;
  summary: string | null;
  author: string | null;
  published_at: string | null;
  created_at: string;
}

export interface PaginatedArticles {
  items: Article[];
  total: number;
  limit: number;
  offset: number;
}

export interface ArticleState {
  article_id: number;
  is_read: boolean;
  is_saved: boolean;
  read_at: string | null;
  saved_at: string | null;
}

export interface GetArticlesParams {
  collectionId: number;
  limit?: number;
  offset?: number;
  unreadOnly?: boolean;
  savedOnly?: boolean;
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

  return response.json();
}

export const articlesApi = {
  /**
   * Fetch articles for a collection with pagination and filters
   */
  async getByCollection(params: GetArticlesParams): Promise<PaginatedArticles> {
    const {
      collectionId,
      limit = 20,
      offset = 0,
      unreadOnly,
      savedOnly,
    } = params;
    const queryParams = new URLSearchParams();
    queryParams.set("limit", String(limit));
    queryParams.set("offset", String(offset));
    if (unreadOnly) queryParams.set("unread_only", "true");
    if (savedOnly) queryParams.set("saved_only", "true");

    return request<PaginatedArticles>(
      `/api/v1/collections/${collectionId}/articles?${queryParams}`,
    );
  },

  /**
   * Mark an article as read
   */
  async markRead(articleId: number): Promise<ArticleState> {
    return request<ArticleState>(`/api/v1/articles/${articleId}/read`, {
      method: "PUT",
    });
  },

  /**
   * Mark an article as unread
   */
  async markUnread(articleId: number): Promise<ArticleState> {
    return request<ArticleState>(`/api/v1/articles/${articleId}/read`, {
      method: "DELETE",
    });
  },

  /**
   * Save an article
   */
  async save(articleId: number): Promise<ArticleState> {
    return request<ArticleState>(`/api/v1/articles/${articleId}/saved`, {
      method: "PUT",
    });
  },

  /**
   * Unsave an article
   */
  async unsave(articleId: number): Promise<ArticleState> {
    return request<ArticleState>(`/api/v1/articles/${articleId}/saved`, {
      method: "DELETE",
    });
  },
};
