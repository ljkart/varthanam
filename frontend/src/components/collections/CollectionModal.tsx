import { useState, type FormEvent } from "react";
import { Modal, Input, Textarea, Button } from "../ui";
import type { Collection } from "../../lib/collectionsApi";
import styles from "./CollectionModal.module.css";

export interface CollectionModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: { name: string; description?: string }) => Promise<void>;
  collection?: Collection | null;
  isLoading?: boolean;
}

/**
 * Modal for creating or editing a collection.
 * If collection prop is provided, it's in edit mode.
 */
export function CollectionModal({
  isOpen,
  onClose,
  onSubmit,
  collection,
  isLoading = false,
}: CollectionModalProps) {
  // Use key-based reset by rendering inner component only when open
  if (!isOpen) return null;

  return (
    <CollectionModalContent
      onClose={onClose}
      onSubmit={onSubmit}
      collection={collection}
      isLoading={isLoading}
    />
  );
}

interface CollectionModalContentProps {
  onClose: () => void;
  onSubmit: (data: { name: string; description?: string }) => Promise<void>;
  collection?: Collection | null;
  isLoading?: boolean;
}

function CollectionModalContent({
  onClose,
  onSubmit,
  collection,
  isLoading = false,
}: CollectionModalContentProps) {
  const [name, setName] = useState(collection?.name || "");
  const [description, setDescription] = useState(collection?.description || "");
  const [error, setError] = useState("");

  const isEditMode = !!collection;
  const title = isEditMode ? "Edit Collection" : "Create Collection";

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");

    const trimmedName = name.trim();
    if (!trimmedName) {
      setError("Collection name is required");
      return;
    }

    try {
      await onSubmit({
        name: trimmedName,
        description: description.trim() || undefined,
      });
      onClose();
    } catch (err) {
      const apiError = err as { detail?: string };
      setError(apiError.detail || "Failed to save collection");
    }
  }

  return (
    <Modal
      isOpen={true}
      onClose={onClose}
      title={title}
      footer={
        <div className={styles.footer}>
          <div />
          <div className={styles.actions}>
            <Button variant="secondary" onClick={onClose} type="button">
              Cancel
            </Button>
            <Button type="submit" form="collection-form" isLoading={isLoading}>
              {isEditMode ? "Save Changes" : "Create Collection"}
            </Button>
          </div>
        </div>
      }
    >
      <form
        id="collection-form"
        onSubmit={handleSubmit}
        className={styles.form}
      >
        {error && <div className={styles.error}>{error}</div>}

        <Input
          label="Collection Name"
          placeholder="e.g., Tech News"
          value={name}
          onChange={(e) => setName(e.target.value)}
          autoFocus
        />

        <Textarea
          label="Description (optional)"
          placeholder="Describe what this collection is about..."
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          rows={3}
        />
      </form>
    </Modal>
  );
}
