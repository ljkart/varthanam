/**
 * API client for rules operations.
 *
 * Provides typed functions for CRUD operations on rules.
 * All endpoints require authentication via the Authorization header.
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

export interface ApiError {
  detail: string;
  status: number;
}

/**
 * Rule data structure from the API.
 */
export interface Rule {
  id: number;
  name: string;
  include_keywords: string | null;
  exclude_keywords: string | null;
  collection_id: number | null;
  frequency_minutes: number;
  last_run_at: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

/**
 * Payload for creating a new rule.
 */
export interface RuleCreate {
  name: string;
  frequency_minutes: number;
  include_keywords?: string | null;
  exclude_keywords?: string | null;
  collection_id?: number | null;
  is_active?: boolean;
}

/**
 * Payload for updating an existing rule.
 * All fields are optional - only provided fields will be updated.
 */
export interface RuleUpdate {
  name?: string;
  frequency_minutes?: number;
  include_keywords?: string | null;
  exclude_keywords?: string | null;
  collection_id?: number | null;
  is_active?: boolean;
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

/**
 * Rules API client with typed methods for all rule operations.
 */
export const rulesApi = {
  /**
   * List all rules for the current user.
   */
  async list(): Promise<Rule[]> {
    return request<Rule[]>("/api/v1/rules", { method: "GET" });
  },

  /**
   * Get a single rule by ID.
   */
  async get(ruleId: number): Promise<Rule> {
    return request<Rule>(`/api/v1/rules/${ruleId}`, { method: "GET" });
  },

  /**
   * Create a new rule.
   */
  async create(data: RuleCreate): Promise<Rule> {
    return request<Rule>("/api/v1/rules", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  /**
   * Update an existing rule.
   */
  async update(ruleId: number, data: RuleUpdate): Promise<Rule> {
    return request<Rule>(`/api/v1/rules/${ruleId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  },

  /**
   * Delete a rule.
   */
  async delete(ruleId: number): Promise<Rule> {
    return request<Rule>(`/api/v1/rules/${ruleId}`, { method: "DELETE" });
  },

  /**
   * Toggle rule active state.
   */
  async toggleActive(ruleId: number, isActive: boolean): Promise<Rule> {
    return request<Rule>(`/api/v1/rules/${ruleId}`, {
      method: "PATCH",
      body: JSON.stringify({ is_active: isActive }),
    });
  },
};
