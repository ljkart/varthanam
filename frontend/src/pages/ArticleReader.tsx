import { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Button } from "../components/ui";
import { articlesApi, type ArticleState } from "../lib/articlesApi";
import styles from "./ArticleReader.module.css";

/**
 * Article reader page for viewing a single article.
 * Note: Backend doesn't have a single article GET endpoint, so we show
 * article info from URL params and provide actions.
 */
export function ArticleReaderPage() {
  const { articleId } = useParams<{ articleId: string }>();
  const navigate = useNavigate();
  const [articleState, setArticleState] = useState<ArticleState | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const id = articleId ? parseInt(articleId, 10) : null;

  async function handleMarkRead() {
    if (!id) return;
    setIsLoading(true);
    try {
      const state = await articlesApi.markRead(id);
      setArticleState(state);
    } catch {
      // Silently fail
    } finally {
      setIsLoading(false);
    }
  }

  async function handleToggleSave() {
    if (!id) return;
    setIsLoading(true);
    try {
      if (articleState?.is_saved) {
        const state = await articlesApi.unsave(id);
        setArticleState(state);
      } else {
        const state = await articlesApi.save(id);
        setArticleState(state);
      }
    } catch {
      // Silently fail
    } finally {
      setIsLoading(false);
    }
  }

  function handleBack() {
    navigate(-1);
  }

  if (!id) {
    return (
      <div className={styles.notFound}>
        <h1 className={styles.notFoundTitle}>Article not found</h1>
        <p className={styles.notFoundText}>
          The article you're looking for doesn't exist.
        </p>
        <Button onClick={() => navigate("/app")}>Back to Dashboard</Button>
      </div>
    );
  }

  return (
    <div className={styles.page}>
      {/* Sidebar */}
      <aside className={styles.sidebar}>
        <button
          type="button"
          className={styles.backButton}
          onClick={handleBack}
        >
          <ArrowLeftIcon />
          Back to feed
        </button>

        <div className={styles.relatedSection}>
          <div className={styles.relatedHeader}>
            <h2 className={styles.relatedTitle}>Article Actions</h2>
            <p className={styles.relatedSubtitle}>Manage this article</p>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            <Button
              variant="secondary"
              onClick={handleMarkRead}
              disabled={isLoading || articleState?.is_read}
              leftIcon={<CheckIcon />}
            >
              {articleState?.is_read ? "Marked as Read" : "Mark as Read"}
            </Button>
            <Button
              variant={articleState?.is_saved ? "primary" : "secondary"}
              onClick={handleToggleSave}
              disabled={isLoading}
              leftIcon={<BookmarkIcon filled={articleState?.is_saved} />}
            >
              {articleState?.is_saved ? "Saved" : "Save Article"}
            </Button>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <main className={styles.main}>
        {/* Article header */}
        <div className={styles.articleHeader}>
          <div className={styles.articleActions}>
            <button
              type="button"
              className={`${styles.actionButton} ${articleState?.is_read ? styles.active : ""}`}
              onClick={handleMarkRead}
              disabled={isLoading}
            >
              <CheckIcon />
              {articleState?.is_read ? "Read" : "Mark read"}
            </button>
            <button
              type="button"
              className={`${styles.actionButton} ${articleState?.is_saved ? styles.primary : ""}`}
              onClick={handleToggleSave}
              disabled={isLoading}
            >
              <BookmarkIcon filled={articleState?.is_saved} />
              {articleState?.is_saved ? "Saved" : "Save"}
            </button>
            <button type="button" className={styles.actionButton}>
              <ShareIcon />
              Share
            </button>
          </div>
          <span className={styles.readProgress}>Article #{id}</span>
        </div>

        {/* Article content */}
        <div className={styles.articleContent}>
          <div className={styles.articleMeta}>
            <div className={styles.articleSourceRow}>
              <div className={styles.sourceIcon}>
                <RssIcon />
              </div>
              <span className={styles.sourceName}>RSS Feed</span>
            </div>

            <h1 className={styles.articleTitle}>Article #{id}</h1>

            <p className={styles.articleDate}>
              View the original article to read the full content.
            </p>
          </div>

          <div className={styles.articleBody}>
            <p>
              This is the article reader view. The full article content is
              available at the original source.
            </p>
            <p>
              Use the buttons above to mark this article as read or save it for
              later. You can also share this article using the share button.
            </p>
            <p>
              Note: The backend API doesn't provide a single-article GET
              endpoint, so the full content is not available here. Visit the
              original URL to read the complete article.
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}

// Icons
function ArrowLeftIcon() {
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
      <line x1="19" y1="12" x2="5" y2="12" />
      <polyline points="12 19 5 12 12 5" />
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

function ShareIcon() {
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
      <circle cx="18" cy="5" r="3" />
      <circle cx="6" cy="12" r="3" />
      <circle cx="18" cy="19" r="3" />
      <line x1="8.59" y1="13.51" x2="15.42" y2="17.49" />
      <line x1="15.41" y1="6.51" x2="8.59" y2="10.49" />
    </svg>
  );
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
