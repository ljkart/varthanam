import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, act, waitFor } from "@testing-library/react";
import { useRules } from "./useRules";
import { rulesApi } from "../lib/rulesApi";
import type { Rule } from "../lib/rulesApi";

// Mock the rulesApi
vi.mock("../lib/rulesApi", () => ({
  rulesApi: {
    list: vi.fn(),
    get: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
    toggleActive: vi.fn(),
  },
}));

const mockRule: Rule = {
  id: 1,
  name: "Tech News",
  include_keywords: "technology,ai",
  exclude_keywords: "crypto",
  collection_id: 1,
  frequency_minutes: 60,
  last_run_at: null,
  is_active: true,
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
};

describe("useRules", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("fetches rules on mount", async () => {
    vi.mocked(rulesApi.list).mockResolvedValue([mockRule]);

    const { result } = renderHook(() => useRules());

    await waitFor(() => {
      expect(result.current.rules).toHaveLength(1);
    });

    expect(rulesApi.list).toHaveBeenCalled();
    expect(result.current.rules[0].name).toBe("Tech News");
  });

  it("sets loading state during fetch", async () => {
    let resolvePromise: (value: Rule[]) => void;
    vi.mocked(rulesApi.list).mockReturnValue(
      new Promise((resolve) => {
        resolvePromise = resolve;
      }),
    );

    const { result } = renderHook(() => useRules());

    expect(result.current.isLoading).toBe(true);

    await act(async () => {
      resolvePromise!([mockRule]);
    });

    expect(result.current.isLoading).toBe(false);
  });

  it("handles fetch errors", async () => {
    vi.mocked(rulesApi.list).mockRejectedValue({
      detail: "Failed to load rules",
    });

    const { result } = renderHook(() => useRules());

    await waitFor(() => {
      expect(result.current.error).toBe("Failed to load rules");
    });

    expect(result.current.rules).toHaveLength(0);
  });

  it("creates a new rule", async () => {
    vi.mocked(rulesApi.list).mockResolvedValue([]);
    vi.mocked(rulesApi.create).mockResolvedValue(mockRule);

    const { result } = renderHook(() => useRules());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    await act(async () => {
      await result.current.createRule({
        name: "Tech News",
        frequency_minutes: 60,
        include_keywords: "technology,ai",
        exclude_keywords: "crypto",
        collection_id: 1,
      });
    });

    expect(rulesApi.create).toHaveBeenCalled();
    expect(result.current.rules).toHaveLength(1);
  });

  it("updates an existing rule", async () => {
    vi.mocked(rulesApi.list).mockResolvedValue([mockRule]);
    const updatedRule = { ...mockRule, name: "Updated Rule" };
    vi.mocked(rulesApi.update).mockResolvedValue(updatedRule);

    const { result } = renderHook(() => useRules());

    await waitFor(() => {
      expect(result.current.rules).toHaveLength(1);
    });

    await act(async () => {
      await result.current.updateRule(1, { name: "Updated Rule" });
    });

    expect(rulesApi.update).toHaveBeenCalledWith(1, { name: "Updated Rule" });
    expect(result.current.rules[0].name).toBe("Updated Rule");
  });

  it("deletes a rule", async () => {
    vi.mocked(rulesApi.list).mockResolvedValue([mockRule]);
    vi.mocked(rulesApi.delete).mockResolvedValue(mockRule);

    const { result } = renderHook(() => useRules());

    await waitFor(() => {
      expect(result.current.rules).toHaveLength(1);
    });

    await act(async () => {
      await result.current.deleteRule(1);
    });

    expect(rulesApi.delete).toHaveBeenCalledWith(1);
    expect(result.current.rules).toHaveLength(0);
  });

  it("toggles rule active state", async () => {
    vi.mocked(rulesApi.list).mockResolvedValue([mockRule]);
    const toggledRule = { ...mockRule, is_active: false };
    vi.mocked(rulesApi.toggleActive).mockResolvedValue(toggledRule);

    const { result } = renderHook(() => useRules());

    await waitFor(() => {
      expect(result.current.rules).toHaveLength(1);
    });

    await act(async () => {
      await result.current.toggleRuleActive(1);
    });

    expect(rulesApi.toggleActive).toHaveBeenCalledWith(1, false);
    expect(result.current.rules[0].is_active).toBe(false);
  });

  it("clears error", async () => {
    vi.mocked(rulesApi.list).mockRejectedValue({
      detail: "Error",
    });

    const { result } = renderHook(() => useRules());

    await waitFor(() => {
      expect(result.current.error).toBe("Error");
    });

    act(() => {
      result.current.clearError();
    });

    expect(result.current.error).toBeNull();
  });

  it("handles create error", async () => {
    vi.mocked(rulesApi.list).mockResolvedValue([]);
    vi.mocked(rulesApi.create).mockRejectedValue({
      detail: "Validation error",
    });

    const { result } = renderHook(() => useRules());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    await act(async () => {
      const created = await result.current.createRule({
        name: "Test",
        frequency_minutes: 60,
      });
      expect(created).toBeNull();
    });

    expect(result.current.error).toBe("Validation error");
  });

  it("handles update error", async () => {
    vi.mocked(rulesApi.list).mockResolvedValue([mockRule]);
    vi.mocked(rulesApi.update).mockRejectedValue({
      detail: "Update failed",
    });

    const { result } = renderHook(() => useRules());

    await waitFor(() => {
      expect(result.current.rules).toHaveLength(1);
    });

    await act(async () => {
      const updated = await result.current.updateRule(1, { name: "New" });
      expect(updated).toBeNull();
    });

    expect(result.current.error).toBe("Update failed");
  });

  it("handles delete error", async () => {
    vi.mocked(rulesApi.list).mockResolvedValue([mockRule]);
    vi.mocked(rulesApi.delete).mockRejectedValue({
      detail: "Delete failed",
    });

    const { result } = renderHook(() => useRules());

    await waitFor(() => {
      expect(result.current.rules).toHaveLength(1);
    });

    await act(async () => {
      const deleted = await result.current.deleteRule(1);
      expect(deleted).toBe(false);
    });

    expect(result.current.error).toBe("Delete failed");
    expect(result.current.rules).toHaveLength(1);
  });

  it("handles toggle error", async () => {
    vi.mocked(rulesApi.list).mockResolvedValue([mockRule]);
    vi.mocked(rulesApi.toggleActive).mockRejectedValue({
      detail: "Toggle failed",
    });

    const { result } = renderHook(() => useRules());

    await waitFor(() => {
      expect(result.current.rules).toHaveLength(1);
    });

    await act(async () => {
      const toggled = await result.current.toggleRuleActive(1);
      expect(toggled).toBe(false);
    });

    expect(result.current.error).toBe("Toggle failed");
  });
});
