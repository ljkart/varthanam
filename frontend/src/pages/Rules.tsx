/**
 * Rules management page.
 *
 * Displays user rules with create, edit, delete, and toggle active operations.
 */

import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "../components/ui";
import { RuleCard, RuleModal } from "../components/rules";
import { useRules } from "../hooks/useRules";
import { useCollections } from "../hooks/useCollections";
import type { Rule, RuleCreate, RuleUpdate } from "../lib/rulesApi";
import styles from "./Rules.module.css";

export function RulesPage() {
  const navigate = useNavigate();
  const {
    rules,
    isLoading,
    error,
    createRule,
    updateRule,
    deleteRule,
    toggleRuleActive,
    clearError,
  } = useRules();
  const { collections } = useCollections();

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingRule, setEditingRule] = useState<Rule | null>(null);
  const [deletingRule, setDeletingRule] = useState<Rule | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  function handleCreateClick() {
    setEditingRule(null);
    setIsModalOpen(true);
  }

  function handleEditClick(rule: Rule) {
    setEditingRule(rule);
    setIsModalOpen(true);
  }

  function handleDeleteClick(rule: Rule) {
    setDeletingRule(rule);
  }

  async function handleModalSubmit(data: RuleCreate | RuleUpdate) {
    setIsSubmitting(true);
    try {
      if (editingRule) {
        const result = await updateRule(editingRule.id, data as RuleUpdate);
        if (result) {
          setIsModalOpen(false);
          setEditingRule(null);
        }
      } else {
        const result = await createRule(data as RuleCreate);
        if (result) {
          setIsModalOpen(false);
        }
      }
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleDeleteConfirm() {
    if (!deletingRule) return;
    const success = await deleteRule(deletingRule.id);
    if (success) {
      setDeletingRule(null);
    }
  }

  async function handleToggleActive(rule: Rule) {
    await toggleRuleActive(rule.id);
  }

  function getCollectionName(collectionId: number | null): string | undefined {
    if (!collectionId) return undefined;
    const collection = collections.find((c) => c.id === collectionId);
    return collection?.name;
  }

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <div className={styles.headerContent}>
          <div className={styles.headerLeft}>
            <button
              type="button"
              className={styles.backButton}
              onClick={() => navigate("/app")}
            >
              <ArrowLeftIcon />
              Back
            </button>
            <h1 className={styles.title}>Rules</h1>
          </div>
          <Button onClick={handleCreateClick} leftIcon={<PlusIcon />}>
            Create Rule
          </Button>
        </div>
      </header>

      <main className={styles.content}>
        <div className={styles.intro}>
          <p className={styles.introText}>
            Rules automatically filter and organize articles based on keywords.
            Create rules to surface content that matters to you and filter out
            the noise.
          </p>
        </div>

        {error && (
          <div className={styles.error}>
            <span className={styles.errorMessage}>{error}</span>
            <button
              type="button"
              className={styles.errorClose}
              onClick={clearError}
              aria-label="Dismiss error"
            >
              <CloseIcon />
            </button>
          </div>
        )}

        {isLoading && rules.length === 0 && (
          <div className={styles.loadingState}>
            <div className={styles.spinner} />
            Loading rules...
          </div>
        )}

        {!isLoading && rules.length === 0 && (
          <div className={styles.emptyState}>
            <div className={styles.emptyIcon}>
              <RulesIcon />
            </div>
            <h2 className={styles.emptyTitle}>No rules yet</h2>
            <p className={styles.emptyDescription}>
              Create your first rule to automatically filter and organize
              articles based on keywords.
            </p>
            <Button onClick={handleCreateClick} leftIcon={<PlusIcon />}>
              Create Rule
            </Button>
          </div>
        )}

        {rules.length > 0 && (
          <div className={styles.rulesGrid}>
            {rules.map((rule) => (
              <RuleCard
                key={rule.id}
                rule={rule}
                collectionName={getCollectionName(rule.collection_id)}
                onEdit={() => handleEditClick(rule)}
                onDelete={() => handleDeleteClick(rule)}
                onToggleActive={() => handleToggleActive(rule)}
                disabled={isLoading}
              />
            ))}
          </div>
        )}
      </main>

      <RuleModal
        isOpen={isModalOpen}
        onClose={() => {
          setIsModalOpen(false);
          setEditingRule(null);
        }}
        onSubmit={handleModalSubmit}
        rule={editingRule}
        collections={collections}
        isLoading={isSubmitting}
        error={error}
      />

      {deletingRule && (
        <div
          className={styles.deleteOverlay}
          onClick={(e) => e.target === e.currentTarget && setDeletingRule(null)}
          role="dialog"
          aria-modal="true"
          aria-labelledby="delete-modal-title"
        >
          <div className={styles.deleteModal}>
            <div className={styles.deleteIcon}>
              <TrashIcon />
            </div>
            <h2 id="delete-modal-title" className={styles.deleteTitle}>
              Delete Rule
            </h2>
            <p className={styles.deleteDescription}>
              Are you sure you want to delete "{deletingRule.name}"? This action
              cannot be undone.
            </p>
            <div className={styles.deleteActions}>
              <Button variant="secondary" onClick={() => setDeletingRule(null)}>
                Cancel
              </Button>
              <Button
                variant="primary"
                onClick={handleDeleteConfirm}
                isLoading={isLoading}
                style={{ backgroundColor: "var(--color-error)" }}
              >
                Delete
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// Icons
function ArrowLeftIcon() {
  return (
    <svg
      width="16"
      height="16"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <line x1="19" y1="12" x2="5" y2="12" />
      <polyline points="12 19 5 12 12 5" />
    </svg>
  );
}

function PlusIcon() {
  return (
    <svg
      width="16"
      height="16"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <line x1="12" y1="5" x2="12" y2="19" />
      <line x1="5" y1="12" x2="19" y2="12" />
    </svg>
  );
}

function CloseIcon() {
  return (
    <svg
      width="16"
      height="16"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <line x1="18" y1="6" x2="6" y2="18" />
      <line x1="6" y1="6" x2="18" y2="18" />
    </svg>
  );
}

function TrashIcon() {
  return (
    <svg
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <polyline points="3 6 5 6 21 6" />
      <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
    </svg>
  );
}

function RulesIcon() {
  return (
    <svg
      width="32"
      height="32"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M12 20h9" />
      <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z" />
    </svg>
  );
}
