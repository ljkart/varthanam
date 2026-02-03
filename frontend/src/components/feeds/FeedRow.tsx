import type { Feed } from "../../lib/feedsApi";
import styles from "./FeedRow.module.css";

export interface FeedRowProps {
  feed: Feed;
  onAssign: (feed: Feed) => void;
  onDelete?: (feed: Feed) => void;
}

/**
 * Table row component displaying a single feed.
 */
export function FeedRow({ feed, onAssign, onDelete }: FeedRowProps) {
  const isActive = feed.failure_count === 0;
  const lastFetchedText = feed.last_fetched_at
    ? formatTimeAgo(new Date(feed.last_fetched_at))
    : "Never";

  return (
    <div className={styles.row}>
      <div className={styles.nameCell}>
        <RssIcon />
        <span className={styles.name}>{feed.title || "Untitled Feed"}</span>
      </div>
      <div className={styles.urlCell}>
        <span className={styles.url}>{truncateUrl(feed.url)}</span>
      </div>
      <div className={styles.fetchedCell}>
        <span className={isActive ? styles.fetchedTime : styles.fetchedFailed}>
          {isActive ? lastFetchedText : "Failed"}
        </span>
      </div>
      <div className={styles.statusCell}>
        <span
          className={`${styles.badge} ${isActive ? styles.active : styles.failed}`}
        >
          {isActive ? "Active" : "Failed"}
        </span>
      </div>
      <div className={styles.actionsCell}>
        <button
          type="button"
          className={styles.actionButton}
          onClick={() => onAssign(feed)}
          aria-label={`Assign ${feed.title || "feed"} to collection`}
          title="Assign to collection"
        >
          <FolderPlusIcon />
        </button>
        {onDelete && (
          <button
            type="button"
            className={`${styles.actionButton} ${styles.deleteButton}`}
            onClick={() => onDelete(feed)}
            aria-label={`Delete ${feed.title || "feed"}`}
          >
            <TrashIcon />
          </button>
        )}
      </div>
    </div>
  );
}

function truncateUrl(url: string): string {
  try {
    const parsed = new URL(url);
    const path = parsed.pathname + parsed.search;
    const display = parsed.host + (path.length > 1 ? path : "");
    return display.length > 35 ? display.substring(0, 35) + "..." : display;
  } catch {
    return url.length > 35 ? url.substring(0, 35) + "..." : url;
  }
}

function formatTimeAgo(date: Date): string {
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return "Just now";
  if (diffMins < 60) return `${diffMins} min ago`;
  if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? "s" : ""} ago`;
  return `${diffDays} day${diffDays > 1 ? "s" : ""} ago`;
}

function RssIcon() {
  return (
    <svg
      width="14"
      height="14"
      viewBox="0 0 24 24"
      fill="currentColor"
      stroke="none"
    >
      <circle cx="6.18" cy="17.82" r="2.18" />
      <path d="M4 4.44v2.83c7.03 0 12.73 5.7 12.73 12.73h2.83c0-8.59-6.97-15.56-15.56-15.56z" />
      <path d="M4 10.1v2.83c3.9 0 7.07 3.17 7.07 7.07h2.83c0-5.47-4.43-9.9-9.9-9.9z" />
    </svg>
  );
}

function FolderPlusIcon() {
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
      <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" />
      <line x1="12" y1="11" x2="12" y2="17" />
      <line x1="9" y1="14" x2="15" y2="14" />
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
