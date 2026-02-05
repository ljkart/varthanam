/**
 * Custom hook for managing rules state.
 *
 * Provides CRUD operations for rules with loading and error states.
 */

import { useState, useCallback, useEffect } from "react";
import {
  rulesApi,
  type Rule,
  type RuleCreate,
  type RuleUpdate,
} from "../lib/rulesApi";

interface ApiError {
  detail?: string;
}

export function useRules() {
  const [rules, setRules] = useState<Rule[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchRules = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await rulesApi.list();
      setRules(data);
    } catch (err) {
      const apiError = err as ApiError;
      setError(apiError.detail || "Failed to load rules");
    } finally {
      setIsLoading(false);
    }
  }, []);

  const createRule = useCallback(
    async (data: RuleCreate): Promise<Rule | null> => {
      setIsLoading(true);
      setError(null);
      try {
        const rule = await rulesApi.create(data);
        setRules((prev) => [...prev, rule]);
        return rule;
      } catch (err) {
        const apiError = err as ApiError;
        setError(apiError.detail || "Failed to create rule");
        return null;
      } finally {
        setIsLoading(false);
      }
    },
    [],
  );

  const updateRule = useCallback(
    async (ruleId: number, data: RuleUpdate): Promise<Rule | null> => {
      setIsLoading(true);
      setError(null);
      try {
        const updated = await rulesApi.update(ruleId, data);
        setRules((prev) => prev.map((r) => (r.id === ruleId ? updated : r)));
        return updated;
      } catch (err) {
        const apiError = err as ApiError;
        setError(apiError.detail || "Failed to update rule");
        return null;
      } finally {
        setIsLoading(false);
      }
    },
    [],
  );

  const deleteRule = useCallback(async (ruleId: number): Promise<boolean> => {
    setIsLoading(true);
    setError(null);
    try {
      await rulesApi.delete(ruleId);
      setRules((prev) => prev.filter((r) => r.id !== ruleId));
      return true;
    } catch (err) {
      const apiError = err as ApiError;
      setError(apiError.detail || "Failed to delete rule");
      return false;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const toggleRuleActive = useCallback(
    async (ruleId: number): Promise<boolean> => {
      const rule = rules.find((r) => r.id === ruleId);
      if (!rule) return false;

      setError(null);
      try {
        const updated = await rulesApi.toggleActive(ruleId, !rule.is_active);
        setRules((prev) => prev.map((r) => (r.id === ruleId ? updated : r)));
        return true;
      } catch (err) {
        const apiError = err as ApiError;
        setError(apiError.detail || "Failed to toggle rule");
        return false;
      }
    },
    [rules],
  );

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  // Fetch rules on mount
  useEffect(() => {
    fetchRules();
  }, [fetchRules]);

  return {
    rules,
    isLoading,
    error,
    fetchRules,
    createRule,
    updateRule,
    deleteRule,
    toggleRuleActive,
    clearError,
  };
}
