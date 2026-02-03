import type { Collection } from "../../lib/collectionsApi";
import styles from "./CollectionCard.module.css";

export interface CollectionCardProps {
  collection: Collection;
  onEdit: (collection: Collection) => void;
  onDelete: (collection: Collection) => void;
}

/**
 * Card component displaying a single collection with edit/delete actions.
 */
export function CollectionCard({
  collection,
  onEdit,
  onDelete,
}: CollectionCardProps) {
  return (
    <div className={styles.card}>
      <div className={styles.content}>
        <h3 className={styles.name}>{collection.name}</h3>
        {collection.description && (
          <p className={styles.description}>{collection.description}</p>
        )}
      </div>
      <div className={styles.actions}>
        <button
          type="button"
          className={styles.actionButton}
          onClick={() => onEdit(collection)}
          aria-label={`Edit ${collection.name}`}
        >
          <EditIcon />
        </button>
        <button
          type="button"
          className={`${styles.actionButton} ${styles.deleteButton}`}
          onClick={() => onDelete(collection)}
          aria-label={`Delete ${collection.name}`}
        >
          <TrashIcon />
        </button>
      </div>
    </div>
  );
}

function EditIcon() {
  return (
    <svg
      width="14"
      height="14"
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
      width="14"
      height="14"
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
