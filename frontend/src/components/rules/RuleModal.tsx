/**
 * RuleModal component for creating and editing rules.
 *
 * Uses conditional rendering pattern to reset form state when reopened.
 */

import { useState } from "react";
import { Button } from "../ui";
import type { Rule, RuleCreate, RuleUpdate } from "../../lib/rulesApi";
import type { Collection } from "../../lib/collectionsApi";
import styles from "./RuleModal.module.css";

interface RuleModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: RuleCreate | RuleUpdate) => Promise<void>;
  rule?: Rule | null;
  collections: Collection[];
  isLoading?: boolean;
  error?: string | null;
}

export function RuleModal(props: RuleModalProps) {
  if (!props.isOpen) return null;
  return <RuleModalContent {...props} isOpen={true} />;
}

interface RuleModalContentProps extends Omit<RuleModalProps, "isOpen"> {
  isOpen: true;
}

function RuleModalContent({
  onClose,
  onSubmit,
  rule,
  collections,
  isLoading = false,
  error,
}: RuleModalContentProps) {
  const isEditing = !!rule;

  const [name, setName] = useState(rule?.name || "");
  const [includeKeywords, setIncludeKeywords] = useState(
    rule?.include_keywords || "",
  );
  const [excludeKeywords, setExcludeKeywords] = useState(
    rule?.exclude_keywords || "",
  );
  const [collectionId, setCollectionId] = useState<number | null>(
    rule?.collection_id || null,
  );
  const [frequencyMinutes, setFrequencyMinutes] = useState(
    rule?.frequency_minutes?.toString() || "60",
  );
  const [isActive, setIsActive] = useState(rule?.is_active ?? true);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();

    const data: RuleCreate | RuleUpdate = {
      name: name.trim(),
      frequency_minutes: parseInt(frequencyMinutes, 10),
      include_keywords: includeKeywords.trim() || null,
      exclude_keywords: excludeKeywords.trim() || null,
      collection_id: collectionId,
      is_active: isActive,
    };

    await onSubmit(data);
  }

  function handleOverlayClick(e: React.MouseEvent) {
    if (e.target === e.currentTarget) {
      onClose();
    }
  }

  const isValid = name.trim().length > 0 && parseInt(frequencyMinutes, 10) > 0;

  return (
    <div
      className={styles.overlay}
      onClick={handleOverlayClick}
      role="dialog"
      aria-modal="true"
      aria-labelledby="rule-modal-title"
    >
      <div className={styles.modal}>
        <div className={styles.header}>
          <h2 id="rule-modal-title" className={styles.title}>
            {isEditing ? "Edit Rule" : "Create Rule"}
          </h2>
          <button
            type="button"
            className={styles.closeButton}
            onClick={onClose}
            aria-label="Close"
          >
            <CloseIcon />
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className={styles.body}>
            {error && <div className={styles.error}>{error}</div>}

            <div className={styles.field}>
              <label htmlFor="rule-name" className={styles.label}>
                Rule Name
              </label>
              <input
                id="rule-name"
                type="text"
                className={styles.input}
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g., Tech News Alert"
                required
              />
            </div>

            <div className={styles.field}>
              <label htmlFor="include-keywords" className={styles.label}>
                Include Keywords
              </label>
              <input
                id="include-keywords"
                type="text"
                className={styles.input}
                value={includeKeywords}
                onChange={(e) => setIncludeKeywords(e.target.value)}
                placeholder="technology, ai, machine learning"
              />
              <span className={styles.hint}>
                Comma-separated. Articles must contain at least one.
              </span>
            </div>

            <div className={styles.field}>
              <label htmlFor="exclude-keywords" className={styles.label}>
                Exclude Keywords
              </label>
              <input
                id="exclude-keywords"
                type="text"
                className={styles.input}
                value={excludeKeywords}
                onChange={(e) => setExcludeKeywords(e.target.value)}
                placeholder="spam, advertisement"
              />
              <span className={styles.hint}>
                Comma-separated. Articles with these are filtered out.
              </span>
            </div>

            <div className={styles.field}>
              <label htmlFor="collection" className={styles.label}>
                Collection Scope
              </label>
              <select
                id="collection"
                className={styles.select}
                value={collectionId || ""}
                onChange={(e) =>
                  setCollectionId(
                    e.target.value ? parseInt(e.target.value, 10) : null,
                  )
                }
              >
                <option value="">All Collections</option>
                {collections.map((collection) => (
                  <option key={collection.id} value={collection.id}>
                    {collection.name}
                  </option>
                ))}
              </select>
              <span className={styles.hint}>
                Optionally limit the rule to a specific collection.
              </span>
            </div>

            <div className={styles.field}>
              <label htmlFor="frequency" className={styles.label}>
                Check Frequency
              </label>
              <select
                id="frequency"
                className={styles.select}
                value={frequencyMinutes}
                onChange={(e) => setFrequencyMinutes(e.target.value)}
              >
                <option value="15">Every 15 minutes</option>
                <option value="30">Every 30 minutes</option>
                <option value="60">Every hour</option>
                <option value="180">Every 3 hours</option>
                <option value="360">Every 6 hours</option>
                <option value="720">Every 12 hours</option>
                <option value="1440">Every day</option>
              </select>
            </div>

            <div className={styles.toggle}>
              <div className={styles.toggleLabel}>
                <span className={styles.toggleTitle}>Active</span>
                <span className={styles.toggleDescription}>
                  Enable or disable this rule
                </span>
              </div>
              <button
                type="button"
                className={`${styles.switch} ${isActive ? styles.active : ""}`}
                onClick={() => setIsActive(!isActive)}
                role="switch"
                aria-checked={isActive}
                aria-label="Toggle rule active state"
              >
                <span className={styles.switchThumb} />
              </button>
            </div>
          </div>

          <div className={styles.footer}>
            <Button type="button" variant="secondary" onClick={onClose}>
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={!isValid || isLoading}
              isLoading={isLoading}
            >
              {isEditing ? "Save Changes" : "Create Rule"}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}

function CloseIcon() {
  return (
    <svg
      width="20"
      height="20"
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
