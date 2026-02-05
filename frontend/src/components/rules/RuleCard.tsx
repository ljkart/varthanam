/**
 * RuleCard component for displaying a single rule.
 *
 * Shows rule name, status, keywords, and metadata with edit/delete actions.
 */

import type { Rule } from "../../lib/rulesApi";
import styles from "./RuleCard.module.css";

interface RuleCardProps {
  rule: Rule;
  collectionName?: string;
  onEdit?: () => void;
  onDelete?: () => void;
  onToggleActive?: () => void;
  disabled?: boolean;
}

export function RuleCard({
  rule,
  collectionName,
  onEdit,
  onDelete,
  onToggleActive,
  disabled = false,
}: RuleCardProps) {
  const includeKeywords =
    rule.include_keywords?.split(",").map((k) => k.trim()) || [];
  const excludeKeywords =
    rule.exclude_keywords?.split(",").map((k) => k.trim()) || [];

  function formatFrequency(minutes: number): string {
    if (minutes < 60) {
      return `Every ${minutes} min`;
    }
    const hours = Math.floor(minutes / 60);
    if (hours < 24) {
      return `Every ${hours}h`;
    }
    const days = Math.floor(hours / 24);
    return `Every ${days}d`;
  }

  function formatLastRun(dateString: string | null): string {
    if (!dateString) return "Never run";
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);

    if (diffMins < 1) return "Just now";
    if (diffMins < 60) return `${diffMins}m ago`;
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours}h ago`;
    const diffDays = Math.floor(diffHours / 24);
    return `${diffDays}d ago`;
  }

  return (
    <div className={`${styles.card} ${!rule.is_active ? styles.inactive : ""}`}>
      <div className={styles.header}>
        <div className={styles.titleRow}>
          <h3 className={styles.name}>{rule.name}</h3>
          <span
            className={`${styles.statusBadge} ${rule.is_active ? styles.active : styles.paused}`}
          >
            <span className={styles.statusDot} />
            {rule.is_active ? "Active" : "Paused"}
          </span>
        </div>

        <div className={styles.actions}>
          {onToggleActive && (
            <button
              type="button"
              className={styles.actionButton}
              onClick={onToggleActive}
              disabled={disabled}
              aria-label={rule.is_active ? "Pause rule" : "Activate rule"}
            >
              {rule.is_active ? <PauseIcon /> : <PlayIcon />}
            </button>
          )}
          {onEdit && (
            <button
              type="button"
              className={styles.actionButton}
              onClick={onEdit}
              disabled={disabled}
              aria-label="Edit rule"
            >
              <EditIcon />
            </button>
          )}
          {onDelete && (
            <button
              type="button"
              className={`${styles.actionButton} ${styles.danger}`}
              onClick={onDelete}
              disabled={disabled}
              aria-label="Delete rule"
            >
              <TrashIcon />
            </button>
          )}
        </div>
      </div>

      <div className={styles.keywords}>
        {includeKeywords.length > 0 && (
          <div className={styles.keywordRow}>
            <span className={styles.keywordLabel}>Include:</span>
            <div className={styles.keywordTags}>
              {includeKeywords.map((keyword, i) => (
                <span
                  key={i}
                  className={`${styles.keywordTag} ${styles.include}`}
                >
                  {keyword}
                </span>
              ))}
            </div>
          </div>
        )}
        {excludeKeywords.length > 0 && (
          <div className={styles.keywordRow}>
            <span className={styles.keywordLabel}>Exclude:</span>
            <div className={styles.keywordTags}>
              {excludeKeywords.map((keyword, i) => (
                <span
                  key={i}
                  className={`${styles.keywordTag} ${styles.exclude}`}
                >
                  {keyword}
                </span>
              ))}
            </div>
          </div>
        )}
        {includeKeywords.length === 0 && excludeKeywords.length === 0 && (
          <div className={styles.keywordRow}>
            <span className={styles.keywordLabel}>No keywords configured</span>
          </div>
        )}
      </div>

      <div className={styles.meta}>
        <span className={styles.metaItem}>
          <ClockIcon className={styles.metaIcon} />
          {formatFrequency(rule.frequency_minutes)}
        </span>
        {collectionName && (
          <span className={styles.metaItem}>
            <FolderIcon className={styles.metaIcon} />
            {collectionName}
          </span>
        )}
        <span className={styles.metaItem}>
          <RefreshIcon className={styles.metaIcon} />
          {formatLastRun(rule.last_run_at)}
        </span>
      </div>
    </div>
  );
}

// Icons
function PlayIcon() {
  return (
    <svg
      width="16"
      height="16"
      viewBox="0 0 24 24"
      fill="currentColor"
      stroke="none"
    >
      <polygon points="5 3 19 12 5 21 5 3" />
    </svg>
  );
}

function PauseIcon() {
  return (
    <svg
      width="16"
      height="16"
      viewBox="0 0 24 24"
      fill="currentColor"
      stroke="none"
    >
      <rect x="6" y="4" width="4" height="16" />
      <rect x="14" y="4" width="4" height="16" />
    </svg>
  );
}

function EditIcon() {
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
      <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
      <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
    </svg>
  );
}

function TrashIcon() {
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
      <polyline points="3 6 5 6 21 6" />
      <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
    </svg>
  );
}

function ClockIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <circle cx="12" cy="12" r="10" />
      <polyline points="12 6 12 12 16 14" />
    </svg>
  );
}

function FolderIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" />
    </svg>
  );
}

function RefreshIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <polyline points="23 4 23 10 17 10" />
      <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" />
    </svg>
  );
}
