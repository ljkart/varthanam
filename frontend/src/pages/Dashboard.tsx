import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "../components/ui";
import { ArticleCard, ArticleReaderPanel } from "../components/articles";
import { useCollections } from "../hooks/useCollections";
import { useArticles, type FilterType } from "../hooks/useArticles";
import { useAuth } from "../lib/auth";
import type { Article } from "../lib/articlesApi";
import styles from "./Dashboard.module.css";

export type ViewMode = "stacked" | "grid";

/**
 * Main dashboard page with sidebar navigation, article list/grid, and slide-in reader.
 */
export function DashboardPage() {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const { collections, isLoading: isCollectionsLoading } = useCollections();
  const {
    articles,
    total,
    isLoading: isArticlesLoading,
    hasMore,
    filter,
    fetchArticles,
    loadMore,
    setFilter,
    markRead,
    saveArticle,
    unsaveArticle,
  } = useArticles();

  const [selectedCollectionId, setSelectedCollectionId] = useState<
    number | null
  >(null);
  const [articleStates, setArticleStates] = useState<
    Record<number, { isRead: boolean; isSaved: boolean }>
  >({});
  const [viewMode, setViewMode] = useState<ViewMode>("stacked");
  const [selectedArticle, setSelectedArticle] = useState<Article | null>(null);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  // Derive the active collection ID - use selected or default to first
  const activeCollectionId =
    selectedCollectionId ?? (collections.length > 0 ? collections[0].id : null);

  // Track the last fetched collection/filter to avoid redundant fetches
  const lastFetchRef = useRef<{
    collectionId: number | null;
    filter: FilterType;
  } | null>(null);

  // Fetch articles when active collection or filter changes
  useEffect(() => {
    if (activeCollectionId === null) return;

    const shouldFetch =
      lastFetchRef.current === null ||
      lastFetchRef.current.collectionId !== activeCollectionId ||
      lastFetchRef.current.filter !== filter;

    if (shouldFetch) {
      lastFetchRef.current = { collectionId: activeCollectionId, filter };
      fetchArticles(activeCollectionId, true);
    }
  }, [activeCollectionId, filter, fetchArticles]);

  function handleCollectionSelect(id: number) {
    setSelectedCollectionId(id);
    setArticleStates({});
  }

  function handleFilterChange(newFilter: FilterType) {
    setFilter(newFilter);
    setArticleStates({});
  }

  async function handleMarkRead(articleId: number) {
    try {
      await markRead(articleId);
      setArticleStates((prev) => ({
        ...prev,
        [articleId]: { ...prev[articleId], isRead: true },
      }));
    } catch {
      // Error handled in hook
    }
  }

  async function handleSaveToggle(articleId: number) {
    const current = articleStates[articleId];
    const isSaved = current?.isSaved ?? false;

    try {
      if (isSaved) {
        await unsaveArticle(articleId);
      } else {
        await saveArticle(articleId);
      }
      setArticleStates((prev) => ({
        ...prev,
        [articleId]: { ...prev[articleId], isSaved: !isSaved },
      }));
    } catch {
      // Error handled in hook
    }
  }

  function handleArticleClick(article: Article) {
    setSelectedArticle(article);
  }

  function handleCloseReader() {
    setSelectedArticle(null);
  }

  function handleLogout() {
    logout();
    navigate("/login");
  }

  const selectedCollection = collections.find(
    (c) => c.id === activeCollectionId,
  );

  return (
    <div className={styles.page}>
      {/* Sidebar */}
      <aside
        className={`${styles.sidebar} ${sidebarCollapsed ? styles.sidebarCollapsed : ""}`}
      >
        <div className={styles.sidebarTop}>
          <div className={styles.logo}>
            <div className={styles.logoMark} />
            <span className={styles.logoText}>VARTHANAM</span>
          </div>

          {/* Navigation */}
          <nav className={styles.navSection}>
            <button
              type="button"
              className={`${styles.navItem} ${filter === "all" ? styles.active : ""}`}
              onClick={() => handleFilterChange("all")}
            >
              <CalendarIcon className={styles.navIcon} />
              Today
            </button>
            <button
              type="button"
              className={`${styles.navItem} ${filter === "unread" ? styles.active : ""}`}
              onClick={() => handleFilterChange("unread")}
            >
              <InboxIcon className={styles.navIcon} />
              Unread
            </button>
            <button
              type="button"
              className={`${styles.navItem} ${filter === "saved" ? styles.active : ""}`}
              onClick={() => handleFilterChange("saved")}
            >
              <BookmarkIcon className={styles.navIcon} />
              Saved
            </button>
          </nav>

          {/* Collections */}
          <div className={styles.collectionSection}>
            <div className={styles.collectionHeader}>
              <span className={styles.collectionTitle}>COLLECTIONS</span>
              <button
                type="button"
                className={styles.addCollectionBtn}
                onClick={() => navigate("/app/collections")}
                aria-label="Manage collections"
              >
                <PlusIcon />
              </button>
            </div>

            {!isCollectionsLoading && (
              <div className={styles.collectionList}>
                {collections.map((collection) => (
                  <button
                    key={collection.id}
                    type="button"
                    className={`${styles.collectionItem} ${activeCollectionId === collection.id ? styles.active : ""}`}
                    onClick={() => handleCollectionSelect(collection.id)}
                  >
                    <span className={styles.collectionItemLeft}>
                      <FolderIcon className={styles.collectionIcon} />
                      <span className={styles.collectionName}>
                        {collection.name}
                      </span>
                    </span>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        <div className={styles.sidebarBottom}>
          <button
            type="button"
            className={styles.settingsNav}
            onClick={() => navigate("/app/rules")}
          >
            <RulesIcon />
            Rules
          </button>
          <button
            type="button"
            className={styles.settingsNav}
            onClick={() => navigate("/app/feeds")}
          >
            <RssIcon />
            Manage Feeds
          </button>
          <div className={styles.userRow}>
            <div className={styles.userAvatar}>
              {user?.email?.charAt(0).toUpperCase()}
            </div>
            <div className={styles.userInfo}>
              <span className={styles.userName}>{user?.email}</span>
              <button
                type="button"
                onClick={handleLogout}
                style={{
                  background: "none",
                  border: "none",
                  padding: 0,
                  cursor: "pointer",
                }}
              >
                <span className={styles.userEmail}>Sign out</span>
              </button>
            </div>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <main className={styles.main}>
        {/* Top bar */}
        <div className={styles.topBar}>
          <div className={styles.topBarLeft}>
            <button
              type="button"
              className={styles.sidebarToggle}
              onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
              aria-label={
                sidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"
              }
            >
              <MenuIcon />
            </button>
            <div className={styles.searchContainer}>
              <SearchIcon className={styles.searchIcon} />
              <span className={styles.searchPlaceholder}>
                Search articles... (⌘K)
              </span>
            </div>
          </div>
          <div className={styles.topBarRight}>
            <span className={styles.shortcutsHint}>
              j/k navigate · s save · m mark read
            </span>
          </div>
        </div>

        {/* Content area */}
        <div className={styles.content}>
          <div className={styles.contentHeader}>
            <div className={styles.headerLeft}>
              <h1 className={styles.contentTitle}>
                {selectedCollection?.name || "All Articles"}
              </h1>
              <p className={styles.contentSubtitle}>
                {total} article{total !== 1 ? "s" : ""}
                {filter === "unread" && " unread"}
                {filter === "saved" && " saved"}
              </p>
            </div>
            <div className={styles.headerRight}>
              <div
                className={styles.viewToggleGroup}
                role="group"
                aria-label="View mode"
              >
                <button
                  type="button"
                  className={`${styles.viewToggle} ${viewMode === "stacked" ? styles.viewToggleActive : ""}`}
                  onClick={() => setViewMode("stacked")}
                  aria-label="List view"
                  title="List view"
                >
                  <ListIcon />
                </button>
                <button
                  type="button"
                  className={`${styles.viewToggle} ${viewMode === "grid" ? styles.viewToggleActive : ""}`}
                  onClick={() => setViewMode("grid")}
                  aria-label="Grid view"
                  title="Grid view"
                >
                  <LayoutGridIcon />
                </button>
              </div>
            </div>
          </div>

          {/* Loading state */}
          {isArticlesLoading && articles.length === 0 && (
            <div
              className={
                viewMode === "grid" ? styles.articlesGrid : styles.articlesList
              }
            >
              {[1, 2, 3, 4, 5, 6].map((i) => (
                <div key={i} className={styles.skeleton} />
              ))}
            </div>
          )}

          {/* Empty state */}
          {!isArticlesLoading && articles.length === 0 && (
            <div className={styles.emptyState}>
              <div className={styles.emptyIcon}>
                <ArticleIcon />
              </div>
              <h2 className={styles.emptyTitle}>No articles yet</h2>
              <p className={styles.emptyDescription}>
                {collections.length === 0
                  ? "Create a collection and add some feeds to get started."
                  : "Add feeds to this collection to see articles here."}
              </p>
            </div>
          )}

          {/* Articles */}
          {articles.length > 0 && (
            <>
              <div
                className={
                  viewMode === "grid"
                    ? styles.articlesGrid
                    : styles.articlesList
                }
              >
                {articles.map((article) => (
                  <ArticleCard
                    key={article.id}
                    article={article}
                    variant={viewMode}
                    isRead={articleStates[article.id]?.isRead}
                    isSaved={articleStates[article.id]?.isSaved}
                    onClick={() => handleArticleClick(article)}
                    onMarkRead={() => handleMarkRead(article.id)}
                    onSave={() => handleSaveToggle(article.id)}
                  />
                ))}
              </div>

              {/* Load more */}
              {hasMore && (
                <div className={styles.loadMore}>
                  <Button
                    variant="secondary"
                    onClick={() =>
                      activeCollectionId && loadMore(activeCollectionId)
                    }
                    isLoading={isArticlesLoading}
                  >
                    Load more
                  </Button>
                </div>
              )}
            </>
          )}
        </div>
      </main>

      {/* Slide-in reader overlay */}
      {selectedArticle && (
        <div
          className={styles.readerOverlay}
          onClick={handleCloseReader}
          data-testid="reader-overlay"
        >
          <div
            className={styles.readerPanel}
            onClick={(e) => e.stopPropagation()}
          >
            <ArticleReaderPanel
              article={selectedArticle}
              isRead={articleStates[selectedArticle.id]?.isRead}
              isSaved={articleStates[selectedArticle.id]?.isSaved}
              onClose={handleCloseReader}
              onMarkRead={() => handleMarkRead(selectedArticle.id)}
              onSave={() => handleSaveToggle(selectedArticle.id)}
            />
          </div>
        </div>
      )}
    </div>
  );
}

// Icons
function CalendarIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      width="16"
      height="16"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
      <line x1="16" y1="2" x2="16" y2="6" />
      <line x1="8" y1="2" x2="8" y2="6" />
      <line x1="3" y1="10" x2="21" y2="10" />
    </svg>
  );
}

function InboxIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      width="16"
      height="16"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <polyline points="22 12 16 12 14 15 10 15 8 12 2 12" />
      <path d="M5.45 5.11L2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z" />
    </svg>
  );
}

function BookmarkIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      width="16"
      height="16"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z" />
    </svg>
  );
}

function FolderIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
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

function SearchIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      width="16"
      height="16"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <circle cx="11" cy="11" r="8" />
      <line x1="21" y1="21" x2="16.65" y2="16.65" />
    </svg>
  );
}

function RssIcon() {
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
      <circle cx="6.18" cy="17.82" r="2.18" />
      <path d="M4 4.44v2.83c7.03 0 12.73 5.7 12.73 12.73h2.83c0-8.59-6.97-15.56-15.56-15.56z" />
      <path d="M4 10.1v2.83c3.9 0 7.07 3.17 7.07 7.07h2.83c0-5.47-4.43-9.9-9.9-9.9z" />
    </svg>
  );
}

function ArticleIcon() {
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
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
      <polyline points="14 2 14 8 20 8" />
      <line x1="16" y1="13" x2="8" y2="13" />
      <line x1="16" y1="17" x2="8" y2="17" />
      <polyline points="10 9 9 9 8 9" />
    </svg>
  );
}

function RulesIcon() {
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
      <path d="M12 20h9" />
      <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z" />
    </svg>
  );
}

function LayoutGridIcon() {
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
      <rect x="3" y="3" width="7" height="7" />
      <rect x="14" y="3" width="7" height="7" />
      <rect x="14" y="14" width="7" height="7" />
      <rect x="3" y="14" width="7" height="7" />
    </svg>
  );
}

function ListIcon() {
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
      <line x1="8" y1="6" x2="21" y2="6" />
      <line x1="8" y1="12" x2="21" y2="12" />
      <line x1="8" y1="18" x2="21" y2="18" />
      <line x1="3" y1="6" x2="3.01" y2="6" />
      <line x1="3" y1="12" x2="3.01" y2="12" />
      <line x1="3" y1="18" x2="3.01" y2="18" />
    </svg>
  );
}

function MenuIcon() {
  return (
    <svg
      width="20"
      height="20"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <line x1="3" y1="12" x2="21" y2="12" />
      <line x1="3" y1="6" x2="21" y2="6" />
      <line x1="3" y1="18" x2="21" y2="18" />
    </svg>
  );
}
