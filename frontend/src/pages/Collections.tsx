import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "../components/ui";
import {
  CollectionCard,
  CollectionModal,
  DeleteConfirmModal,
} from "../components/collections";
import { useCollections } from "../hooks/useCollections";
import type { Collection } from "../lib/collectionsApi";
import styles from "./Collections.module.css";

/**
 * Collections page - displays all user collections with CRUD operations.
 */
export function CollectionsPage() {
  const navigate = useNavigate();
  const {
    collections,
    isLoading,
    error,
    refetch,
    createCollection,
    updateCollection,
    deleteCollection,
  } = useCollections();

  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [editingCollection, setEditingCollection] = useState<Collection | null>(
    null,
  );
  const [deletingCollection, setDeletingCollection] =
    useState<Collection | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleCreate(data: { name: string; description?: string }) {
    setIsSubmitting(true);
    try {
      await createCollection(data);
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleUpdate(data: { name: string; description?: string }) {
    if (!editingCollection) return;
    setIsSubmitting(true);
    try {
      await updateCollection(editingCollection.id, data);
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleDelete() {
    if (!deletingCollection) return;
    setIsSubmitting(true);
    try {
      await deleteCollection(deletingCollection.id);
    } finally {
      setIsSubmitting(false);
    }
  }

  // Loading state
  if (isLoading) {
    return (
      <div className={styles.page}>
        <div className={styles.header}>
          <div className={styles.headerLeft}>
            <button
              type="button"
              className={styles.backButton}
              onClick={() => navigate("/app")}
            >
              <ArrowLeftIcon />
              Back
            </button>
            <h1 className={styles.title}>Collections</h1>
          </div>
        </div>
        <div className={styles.skeletonList}>
          {[1, 2, 3].map((i) => (
            <div key={i} className={styles.skeleton} />
          ))}
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className={styles.page}>
        <div className={styles.header}>
          <div className={styles.headerLeft}>
            <button
              type="button"
              className={styles.backButton}
              onClick={() => navigate("/app")}
            >
              <ArrowLeftIcon />
              Back
            </button>
            <h1 className={styles.title}>Collections</h1>
          </div>
        </div>
        <div className={styles.errorState}>
          <p className={styles.errorMessage}>{error}</p>
          <Button variant="secondary" onClick={refetch}>
            Try Again
          </Button>
        </div>
      </div>
    );
  }

  // Empty state
  if (collections.length === 0) {
    return (
      <div className={styles.page}>
        <div className={styles.header}>
          <div className={styles.headerLeft}>
            <button
              type="button"
              className={styles.backButton}
              onClick={() => navigate("/app")}
            >
              <ArrowLeftIcon />
              Back
            </button>
            <h1 className={styles.title}>Collections</h1>
          </div>
        </div>
        <div className={styles.emptyState}>
          <div className={styles.emptyIcon}>
            <FolderIcon />
          </div>
          <h2 className={styles.emptyTitle}>No collections yet</h2>
          <p className={styles.emptyDescription}>
            Create your first collection to start organizing your feeds.
          </p>
          <Button
            onClick={() => setIsCreateModalOpen(true)}
            leftIcon={<PlusIcon />}
          >
            Create Collection
          </Button>
        </div>

        <CollectionModal
          isOpen={isCreateModalOpen}
          onClose={() => setIsCreateModalOpen(false)}
          onSubmit={handleCreate}
          isLoading={isSubmitting}
        />
      </div>
    );
  }

  // Normal state with collections
  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <div className={styles.headerLeft}>
          <button
            type="button"
            className={styles.backButton}
            onClick={() => navigate("/app")}
          >
            <ArrowLeftIcon />
            Back
          </button>
          <h1 className={styles.title}>Collections</h1>
        </div>
        <Button
          onClick={() => setIsCreateModalOpen(true)}
          leftIcon={<PlusIcon />}
        >
          New Collection
        </Button>
      </div>

      <div className={styles.list}>
        {collections.map((collection) => (
          <CollectionCard
            key={collection.id}
            collection={collection}
            onEdit={setEditingCollection}
            onDelete={setDeletingCollection}
          />
        ))}
      </div>

      {/* Create Modal */}
      <CollectionModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        onSubmit={handleCreate}
        isLoading={isSubmitting}
      />

      {/* Edit Modal */}
      <CollectionModal
        isOpen={!!editingCollection}
        onClose={() => setEditingCollection(null)}
        onSubmit={handleUpdate}
        collection={editingCollection}
        isLoading={isSubmitting}
      />

      {/* Delete Confirmation Modal */}
      {deletingCollection && (
        <DeleteConfirmModal
          isOpen={!!deletingCollection}
          onClose={() => setDeletingCollection(null)}
          onConfirm={handleDelete}
          collectionName={deletingCollection.name}
          isLoading={isSubmitting}
        />
      )}
    </div>
  );
}

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

function FolderIcon() {
  return (
    <svg
      width="48"
      height="48"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" />
    </svg>
  );
}
