import { useState, type FormEvent } from "react";
import { Modal, Input, Button } from "../ui";
import styles from "./AddFeedModal.module.css";

export interface AddFeedModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (url: string) => Promise<void>;
  isLoading?: boolean;
}

/**
 * Modal for adding a new RSS feed.
 */
export function AddFeedModal({
  isOpen,
  onClose,
  onSubmit,
  isLoading = false,
}: AddFeedModalProps) {
  if (!isOpen) return null;

  return (
    <AddFeedModalContent
      onClose={onClose}
      onSubmit={onSubmit}
      isLoading={isLoading}
    />
  );
}

interface AddFeedModalContentProps {
  onClose: () => void;
  onSubmit: (url: string) => Promise<void>;
  isLoading?: boolean;
}

function AddFeedModalContent({
  onClose,
  onSubmit,
  isLoading = false,
}: AddFeedModalContentProps) {
  const [url, setUrl] = useState("");
  const [error, setError] = useState("");

  function validateUrl(value: string): string | null {
    if (!value.trim()) {
      return "Feed URL is required";
    }
    try {
      const parsed = new URL(value.trim());
      if (!["http:", "https:"].includes(parsed.protocol)) {
        return "URL must start with http:// or https://";
      }
      return null;
    } catch {
      return "Please enter a valid URL";
    }
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");

    const validationError = validateUrl(url);
    if (validationError) {
      setError(validationError);
      return;
    }

    try {
      await onSubmit(url.trim());
      onClose();
    } catch (err) {
      const apiError = err as { detail?: string };
      setError(apiError.detail || "Failed to add feed");
    }
  }

  return (
    <Modal
      isOpen={true}
      onClose={onClose}
      title="Add Feed"
      footer={
        <div className={styles.footer}>
          <div />
          <div className={styles.actions}>
            <Button variant="secondary" onClick={onClose} type="button">
              Cancel
            </Button>
            <Button type="submit" form="add-feed-form" isLoading={isLoading}>
              Add Feed
            </Button>
          </div>
        </div>
      }
    >
      <form id="add-feed-form" onSubmit={handleSubmit} className={styles.form}>
        {error && <div className={styles.error}>{error}</div>}

        <Input
          label="Feed URL"
          type="url"
          placeholder="https://example.com/rss"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          autoFocus
        />

        <p className={styles.hint}>
          Enter the URL of an RSS or Atom feed. We&apos;ll validate and fetch
          the feed content.
        </p>
      </form>
    </Modal>
  );
}
