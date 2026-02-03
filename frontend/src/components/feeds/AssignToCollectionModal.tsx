import { useState } from "react";
import { Modal, Button } from "../ui";
import type { Feed } from "../../lib/feedsApi";
import type { Collection } from "../../lib/collectionsApi";
import styles from "./AssignToCollectionModal.module.css";

export interface AssignToCollectionModalProps {
  isOpen: boolean;
  onClose: () => void;
  onAssign: (collectionId: number) => Promise<void>;
  feed: Feed | null;
  collections: Collection[];
  isLoading?: boolean;
}

/**
 * Modal for assigning a feed to a collection.
 * Uses conditional rendering to reset state when modal reopens.
 */
export function AssignToCollectionModal({
  isOpen,
  onClose,
  onAssign,
  feed,
  collections,
  isLoading = false,
}: AssignToCollectionModalProps) {
  if (!isOpen || !feed) return null;

  return (
    <AssignToCollectionModalContent
      onClose={onClose}
      onAssign={onAssign}
      feed={feed}
      collections={collections}
      isLoading={isLoading}
    />
  );
}

interface AssignToCollectionModalContentProps {
  onClose: () => void;
  onAssign: (collectionId: number) => Promise<void>;
  feed: Feed;
  collections: Collection[];
  isLoading?: boolean;
}

function AssignToCollectionModalContent({
  onClose,
  onAssign,
  feed,
  collections,
  isLoading = false,
}: AssignToCollectionModalContentProps) {
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [error, setError] = useState("");

  async function handleAssign() {
    if (!selectedId) {
      setError("Please select a collection");
      return;
    }

    setError("");
    try {
      await onAssign(selectedId);
      onClose();
    } catch (err) {
      const apiError = err as { detail?: string };
      setError(apiError.detail || "Failed to assign feed to collection");
    }
  }

  return (
    <Modal
      isOpen={true}
      onClose={onClose}
      title="Assign to Collection"
      footer={
        <div className={styles.footer}>
          <div />
          <div className={styles.actions}>
            <Button variant="secondary" onClick={onClose}>
              Cancel
            </Button>
            <Button
              onClick={handleAssign}
              isLoading={isLoading}
              disabled={!selectedId}
            >
              Assign
            </Button>
          </div>
        </div>
      }
    >
      <div className={styles.content}>
        {error && <div className={styles.error}>{error}</div>}

        <p className={styles.feedName}>
          Assign <strong>{feed.title || "Untitled Feed"}</strong> to:
        </p>

        {collections.length === 0 ? (
          <div className={styles.empty}>
            <p>No collections yet.</p>
            <p className={styles.emptyHint}>
              Create a collection first to organize your feeds.
            </p>
          </div>
        ) : (
          <div className={styles.collectionList}>
            {collections.map((collection) => (
              <label
                key={collection.id}
                className={`${styles.collectionItem} ${selectedId === collection.id ? styles.selected : ""}`}
              >
                <input
                  type="radio"
                  name="collection"
                  value={collection.id}
                  checked={selectedId === collection.id}
                  onChange={() => setSelectedId(collection.id)}
                  className={styles.radio}
                />
                <FolderIcon />
                <span className={styles.collectionName}>{collection.name}</span>
              </label>
            ))}
          </div>
        )}
      </div>
    </Modal>
  );
}

function FolderIcon() {
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
      <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" />
    </svg>
  );
}
