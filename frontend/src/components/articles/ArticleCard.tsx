import type { Article } from "../../lib/articlesApi";
import {
  extractImageFromHtml,
  getPlaceholderGradient,
  getPlaceholderLabel,
} from "../../lib/articleImage";
import styles from "./ArticleCard.module.css";

export type ArticleCardVariant = "stacked" | "grid";

export interface ArticleCardProps {
  article: Article;
  variant?: ArticleCardVariant;
  isRead?: boolean;
  isSaved?: boolean;
  onClick?: () => void;
  onMarkRead?: () => void;
  onSave?: () => void;
}

/**
 * Card component displaying an article preview.
 * Supports "stacked" (horizontal list row) and "grid" (vertical card with image) variants.
 */
export function ArticleCard({
  article,
  variant = "stacked",
  isRead = false,
  isSaved = false,
  onClick,
  onMarkRead,
  onSave,
}: ArticleCardProps) {
  const timeAgo = article.published_at
    ? formatTimeAgo(new Date(article.published_at))
    : "Recently";

  const articleImage = extractImageFromHtml(article.summary);
  const gradient = getPlaceholderGradient(article.feed_id);
  const label = getPlaceholderLabel(article.title);

  function handleActionClick(
    e: React.MouseEvent,
    action: (() => void) | undefined,
  ) {
    e.stopPropagation();
    action?.();
  }

  return (
    <article
      className={`${styles.card} ${styles[variant]} ${isRead ? styles.read : ""}`}
      onClick={onClick}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === "Enter" && onClick?.()}
    >
      {/* Grid: full-width image at top */}
      {variant === "grid" && (
        <div
          className={styles.imageContainer}
          style={
            articleImage
              ? { backgroundImage: `url(${articleImage})` }
              : { background: gradient }
          }
          data-testid="article-image"
        >
          {!articleImage && (
            <span className={styles.placeholderLabel}>{label}</span>
          )}
        </div>
      )}

      <div className={styles.contentArea}>
        <div className={styles.source}>
          <span className={styles.sourceIcon}>
            <RssIcon />
          </span>
          <span className={styles.sourceName}>Feed</span>
          {variant === "grid" && (
            <button
              type="button"
              className={`${styles.saveCorner} ${isSaved ? styles.saved : ""}`}
              onClick={(e) => handleActionClick(e, onSave)}
              aria-label={isSaved ? "Unsave" : "Save"}
            >
              <BookmarkIcon filled={isSaved} />
            </button>
          )}
        </div>

        <h3 className={styles.title}>{article.title}</h3>

        {variant === "stacked" && article.summary && (
          <p className={styles.summary}>{stripHtml(article.summary)}</p>
        )}

        <div className={styles.meta}>
          <div className={styles.metaLeft}>
            {article.author && (
              <span className={styles.author}>{article.author}</span>
            )}
            <span className={styles.dot}>·</span>
            <span className={styles.time}>{timeAgo}</span>
          </div>

          {variant === "stacked" && (
            <div className={styles.actions}>
              <button
                type="button"
                className={`${styles.actionButton} ${isRead ? styles.active : ""}`}
                onClick={(e) => handleActionClick(e, onMarkRead)}
                aria-label={isRead ? "Mark as unread" : "Mark as read"}
                title={isRead ? "Mark as unread" : "Mark as read"}
              >
                <CheckIcon />
              </button>
              <button
                type="button"
                className={`${styles.actionButton} ${isSaved ? styles.saved : ""}`}
                onClick={(e) => handleActionClick(e, onSave)}
                aria-label={isSaved ? "Unsave" : "Save"}
                title={isSaved ? "Unsave" : "Save"}
              >
                <BookmarkIcon filled={isSaved} />
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Stacked: small thumbnail on right */}
      {variant === "stacked" && (
        <div
          className={styles.thumbnail}
          style={
            articleImage
              ? { backgroundImage: `url(${articleImage})` }
              : { background: gradient }
          }
          data-testid="article-thumbnail"
        >
          {!articleImage && (
            <span className={styles.placeholderLabelSmall}>{label}</span>
          )}
        </div>
      )}
    </article>
  );
}

function formatTimeAgo(date: Date): string {
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return "Just now";
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  return date.toLocaleDateString();
}

function stripHtml(html: string): string {
  const div = document.createElement("div");
  div.innerHTML = html;
  return div.textContent || div.innerText || "";
}

function RssIcon() {
  return (
    <svg
      width="12"
      height="12"
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

function CheckIcon() {
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
      <polyline points="20 6 9 17 4 12" />
    </svg>
  );
}

function BookmarkIcon({ filled }: { filled?: boolean }) {
  return (
    <svg
      width="14"
      height="14"
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
