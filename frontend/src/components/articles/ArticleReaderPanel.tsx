import { useEffect } from "react";
import type { Article } from "../../lib/articlesApi";
import {
  getPlaceholderGradient,
  getPlaceholderLabel,
} from "../../lib/articleImage";
import styles from "./ArticleReaderPanel.module.css";

export interface ArticleReaderPanelProps {
  article: Article;
  isRead?: boolean;
  isSaved?: boolean;
  onClose: () => void;
  onMarkRead?: () => void;
  onSave?: () => void;
}

/**
 * Slide-in panel displaying a full article.
 * Renders over the dashboard from the right side.
 */
export function ArticleReaderPanel({
  article,
  isRead = false,
  isSaved = false,
  onClose,
  onMarkRead,
  onSave,
}: ArticleReaderPanelProps) {
  // Close on Escape key
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") {
        onClose();
      }
    }
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  const gradient = getPlaceholderGradient(article.feed_id);
  const label = getPlaceholderLabel(article.title);
  const publishedDate = article.published_at
    ? new Date(article.published_at).toLocaleDateString("en-US", {
        year: "numeric",
        month: "long",
        day: "numeric",
      })
    : "Recently";

  return (
    <div className={styles.panel} data-testid="article-reader-panel">
      {/* Sticky header */}
      <div className={styles.header}>
        <button type="button" className={styles.backButton} onClick={onClose}>
          <ArrowLeftIcon />
          <span>Back to feed</span>
        </button>
        <div className={styles.headerActions}>
          <button
            type="button"
            className={`${styles.headerAction} ${isRead ? styles.active : ""}`}
            onClick={onMarkRead}
            aria-label={isRead ? "Mark as unread" : "Mark as read"}
            title={isRead ? "Mark as unread" : "Mark as read"}
          >
            <CheckIcon />
          </button>
          <button
            type="button"
            className={`${styles.headerAction} ${isSaved ? styles.saved : ""}`}
            onClick={onSave}
            aria-label={isSaved ? "Unsave" : "Save"}
            title={isSaved ? "Unsave" : "Save"}
          >
            <BookmarkIcon filled={isSaved} />
          </button>
        </div>
      </div>

      {/* Scrollable content */}
      <div className={styles.body}>
        {/* Hero image placeholder */}
        <div
          className={styles.hero}
          style={{ background: gradient }}
          data-testid="reader-hero"
        >
          <span className={styles.heroLabel}>{label}</span>
        </div>

        {/* Article meta */}
        <div className={styles.meta}>
          <div className={styles.source}>
            <RssIcon />
            <span className={styles.sourceName}>Feed</span>
          </div>
          <h1 className={styles.title}>{article.title}</h1>
          <div className={styles.metaRow}>
            {article.author && (
              <span className={styles.author}>{article.author}</span>
            )}
            {article.author && <span className={styles.dot}>·</span>}
            <span className={styles.date}>{publishedDate}</span>
          </div>
        </div>

        {/* Article body (summary) */}
        {article.summary && (
          <div
            className={styles.content}
            dangerouslySetInnerHTML={{ __html: article.summary }}
          />
        )}

        {/* Visit original link */}
        {article.url && (
          <a
            href={article.url}
            target="_blank"
            rel="noopener noreferrer"
            className={styles.visitLink}
          >
            <ExternalLinkIcon />
            Visit original article
          </a>
        )}
      </div>
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

function CheckIcon() {
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
      <polyline points="20 6 9 17 4 12" />
    </svg>
  );
}

function BookmarkIcon({ filled }: { filled?: boolean }) {
  return (
    <svg
      width="16"
      height="16"
      viewBox="0 0 24 24"
      fill={filled ? "currentColor" : "none"}
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z" />
    </svg>
  );
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

function ExternalLinkIcon() {
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
      <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
      <polyline points="15 3 21 3 21 9" />
      <line x1="10" y1="14" x2="21" y2="3" />
    </svg>
  );
}
