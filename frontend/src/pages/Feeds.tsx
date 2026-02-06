import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "../components/ui";
import {
  AddFeedModal,
  FeedRow,
  AssignToCollectionModal,
} from "../components/feeds";
import { useFeeds } from "../hooks/useFeeds";
import { useCollections } from "../hooks/useCollections";
import { collectionFeedsApi } from "../lib/collectionFeedsApi";
import type { Feed } from "../lib/feedsApi";
import styles from "./Feeds.module.css";

/**
 * Feeds page - displays all user feeds with add and assign operations.
 */
export function FeedsPage() {
  const navigate = useNavigate();
  const { feeds, isLoading: isFeedsLoading, addFeed } = useFeeds();
  const { collections, isLoading: isCollectionsLoading } = useCollections();

  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [assigningFeed, setAssigningFeed] = useState<Feed | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  async function handleAddFeed(url: string) {
    setIsSubmitting(true);
    try {
      const feed = await addFeed({ url });
      setSuccessMessage(`Added "${feed.title || "feed"}" successfully`);
      setTimeout(() => setSuccessMessage(null), 3000);
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleAssignToCollection(collectionId: number) {
    if (!assigningFeed) return;
    setIsSubmitting(true);
    try {
      await collectionFeedsApi.assign(collectionId, assigningFeed.id);
      const collection = collections.find((c) => c.id === collectionId);
      setSuccessMessage(
        `Assigned "${assigningFeed.title}" to "${collection?.name}"`,
      );
      setTimeout(() => setSuccessMessage(null), 3000);
    } finally {
      setIsSubmitting(false);
    }
  }

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
          <div className={styles.titleGroup}>
            <h1 className={styles.title}>Manage Feeds</h1>
            <p className={styles.subtitle}>
              {feeds.length} feed{feeds.length !== 1 ? "s" : ""} connected
            </p>
          </div>
        </div>
        <Button onClick={() => setIsAddModalOpen(true)} leftIcon={<PlusIcon />}>
          Add Feed
        </Button>
      </div>

      {successMessage && <div className={styles.success}>{successMessage}</div>}

      {/* Loading state */}
      {isFeedsLoading && (
        <div className={styles.tableContainer}>
          <div className={styles.table}>
            <div className={styles.tableHeader}>
              <span>FEED NAME</span>
              <span>URL</span>
              <span>LAST FETCHED</span>
              <span>STATUS</span>
              <span>ACTIONS</span>
            </div>
            {[1, 2, 3].map((i) => (
              <div key={i} className={styles.skeleton} />
            ))}
          </div>
        </div>
      )}

      {/* Empty state */}
      {!isFeedsLoading && feeds.length === 0 && (
        <div className={styles.emptyState}>
          <div className={styles.emptyIcon}>
            <RssIcon />
          </div>
          <h2 className={styles.emptyTitle}>No feeds yet</h2>
          <p className={styles.emptyDescription}>
            Add your first RSS feed to start aggregating content.
          </p>
          <Button
            onClick={() => setIsAddModalOpen(true)}
            leftIcon={<PlusIcon />}
          >
            Add Feed
          </Button>
        </div>
      )}

      {/* Feeds table */}
      {!isFeedsLoading && feeds.length > 0 && (
        <div className={styles.tableContainer}>
          <div className={styles.table}>
            <div className={styles.tableHeader}>
              <span className={styles.thName}>FEED NAME</span>
              <span className={styles.thUrl}>URL</span>
              <span className={styles.thFetched}>LAST FETCHED</span>
              <span className={styles.thStatus}>STATUS</span>
              <span className={styles.thActions}>ACTIONS</span>
            </div>
            <div className={styles.tableBody}>
              {feeds.map((feed) => (
                <FeedRow
                  key={feed.id}
                  feed={feed}
                  onAssign={setAssigningFeed}
                />
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Add Feed Modal */}
      <AddFeedModal
        isOpen={isAddModalOpen}
        onClose={() => setIsAddModalOpen(false)}
        onSubmit={handleAddFeed}
        isLoading={isSubmitting}
      />

      {/* Assign to Collection Modal */}
      <AssignToCollectionModal
        isOpen={!!assigningFeed}
        onClose={() => setAssigningFeed(null)}
        onAssign={handleAssignToCollection}
        feed={assigningFeed}
        collections={collections}
        isLoading={isSubmitting || isCollectionsLoading}
      />
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
      width="14"
      height="14"
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

function RssIcon() {
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
      <circle cx="6.18" cy="17.82" r="2.18" />
      <path d="M4 4.44v2.83c7.03 0 12.73 5.7 12.73 12.73h2.83c0-8.59-6.97-15.56-15.56-15.56z" />
      <path d="M4 10.1v2.83c3.9 0 7.07 3.17 7.07 7.07h2.83c0-5.47-4.43-9.9-9.9-9.9z" />
    </svg>
  );
}
