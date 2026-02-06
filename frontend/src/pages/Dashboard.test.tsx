import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, within } from "../test/utils";
import userEvent from "@testing-library/user-event";
import { DashboardPage } from "./Dashboard";
import type { Article } from "../lib/articlesApi";

// Mock hooks
vi.mock("../hooks/useCollections", () => ({
  useCollections: vi.fn(),
}));

vi.mock("../hooks/useArticles", () => ({
  useArticles: vi.fn(),
}));

vi.mock("../lib/auth", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../lib/auth")>();
  return { ...actual, useAuth: vi.fn() };
});

const mockNavigate = vi.fn();
vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return { ...actual, useNavigate: () => mockNavigate };
});

import { useCollections } from "../hooks/useCollections";
import { useArticles } from "../hooks/useArticles";
import { useAuth } from "../lib/auth";

const mockArticles: Article[] = [
  {
    id: 1,
    feed_id: 1,
    title: "First Article",
    url: "https://example.com/1",
    guid: "guid-1",
    summary: "Summary of first article",
    author: "Author One",
    published_at: new Date().toISOString(),
    created_at: new Date().toISOString(),
  },
  {
    id: 2,
    feed_id: 2,
    title: "Second Article",
    url: "https://example.com/2",
    guid: "guid-2",
    summary: "Summary of second article",
    author: "Author Two",
    published_at: new Date().toISOString(),
    created_at: new Date().toISOString(),
  },
];

const defaultUseCollections = {
  collections: [
    {
      id: 1,
      name: "Tech News",
      description: null,
      user_id: 1,
      created_at: "2025-01-01T00:00:00Z",
      updated_at: "2025-01-01T00:00:00Z",
    },
  ],
  isLoading: false,
  error: null,
  refetch: vi.fn(),
  createCollection: vi.fn(),
  updateCollection: vi.fn(),
  deleteCollection: vi.fn(),
};

const defaultUseArticles = {
  articles: mockArticles,
  total: 2,
  isLoading: false,
  error: null,
  hasMore: false,
  filter: "all" as const,
  fetchArticles: vi.fn(),
  loadMore: vi.fn(),
  setFilter: vi.fn(),
  markRead: vi.fn().mockResolvedValue(undefined),
  markUnread: vi.fn().mockResolvedValue(undefined),
  saveArticle: vi.fn().mockResolvedValue(undefined),
  unsaveArticle: vi.fn().mockResolvedValue(undefined),
  clearError: vi.fn(),
};

const defaultUseAuth = {
  user: {
    id: 1,
    email: "user@example.com",
    is_active: true,
    created_at: "2025-01-01T00:00:00Z",
  },
  isLoading: false,
  isAuthenticated: true,
  login: vi.fn(),
  logout: vi.fn(),
};

describe("DashboardPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useCollections).mockReturnValue({ ...defaultUseCollections });
    vi.mocked(useArticles).mockReturnValue({ ...defaultUseArticles });
    vi.mocked(useAuth).mockReturnValue({ ...defaultUseAuth });
  });

  it("renders sidebar with logo", () => {
    render(<DashboardPage />);

    expect(screen.getByText("VARTHANAM")).toBeInTheDocument();
  });

  it("renders sidebar navigation items", () => {
    render(<DashboardPage />);

    expect(screen.getByText("Today")).toBeInTheDocument();
    expect(screen.getByText("Unread")).toBeInTheDocument();
    expect(screen.getByText("Saved")).toBeInTheDocument();
  });

  it("renders collections in sidebar", () => {
    render(<DashboardPage />);

    expect(screen.getByText("COLLECTIONS")).toBeInTheDocument();
    // "Tech News" appears in both sidebar and content title (as active collection)
    expect(screen.getAllByText("Tech News").length).toBeGreaterThanOrEqual(1);
  });

  it("renders article titles in main content", () => {
    render(<DashboardPage />);

    expect(screen.getByText("First Article")).toBeInTheDocument();
    expect(screen.getByText("Second Article")).toBeInTheDocument();
  });

  it("renders article count", () => {
    render(<DashboardPage />);

    expect(screen.getByText("2 articles")).toBeInTheDocument();
  });

  it("defaults to stacked view", () => {
    render(<DashboardPage />);

    const listViewBtn = screen.getByRole("button", { name: /list view/i });
    expect(listViewBtn.className).toMatch(/viewToggleActive/);
  });

  it("renders view toggle buttons", () => {
    render(<DashboardPage />);

    expect(
      screen.getByRole("button", { name: /list view/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /grid view/i }),
    ).toBeInTheDocument();
  });

  it("switches to grid view when grid toggle is clicked", async () => {
    const user = userEvent.setup();
    render(<DashboardPage />);

    const gridBtn = screen.getByRole("button", { name: /grid view/i });
    await user.click(gridBtn);

    expect(gridBtn.className).toMatch(/viewToggleActive/);
  });

  it("switches back to stacked view", async () => {
    const user = userEvent.setup();
    render(<DashboardPage />);

    // Switch to grid first
    await user.click(screen.getByRole("button", { name: /grid view/i }));
    // Switch back to list
    const listBtn = screen.getByRole("button", { name: /list view/i });
    await user.click(listBtn);

    expect(listBtn.className).toMatch(/viewToggleActive/);
  });

  it("opens reader panel when article is clicked", async () => {
    const user = userEvent.setup();
    render(<DashboardPage />);

    await user.click(screen.getByText("First Article"));

    expect(screen.getByTestId("reader-overlay")).toBeInTheDocument();
    expect(screen.getByTestId("article-reader-panel")).toBeInTheDocument();
    // Reader shows the article title
    const readerPanel = screen.getByTestId("article-reader-panel");
    expect(within(readerPanel).getByText("First Article")).toBeInTheDocument();
  });

  it("closes reader panel when backdrop is clicked", async () => {
    const user = userEvent.setup();
    render(<DashboardPage />);

    await user.click(screen.getByText("First Article"));
    expect(screen.getByTestId("reader-overlay")).toBeInTheDocument();

    // Click the overlay backdrop
    await user.click(screen.getByTestId("reader-overlay"));

    expect(screen.queryByTestId("reader-overlay")).not.toBeInTheDocument();
  });

  it("closes reader panel when 'Back to feed' is clicked", async () => {
    const user = userEvent.setup();
    render(<DashboardPage />);

    await user.click(screen.getByText("First Article"));
    expect(screen.getByTestId("article-reader-panel")).toBeInTheDocument();

    await user.click(screen.getByText("Back to feed"));

    expect(
      screen.queryByTestId("article-reader-panel"),
    ).not.toBeInTheDocument();
  });

  it("shows empty state when no articles", () => {
    vi.mocked(useArticles).mockReturnValue({
      ...defaultUseArticles,
      articles: [],
      total: 0,
    });

    render(<DashboardPage />);

    expect(screen.getByText("No articles yet")).toBeInTheDocument();
  });

  it("shows loading skeletons when loading", () => {
    vi.mocked(useArticles).mockReturnValue({
      ...defaultUseArticles,
      articles: [],
      isLoading: true,
    });

    const { container } = render(<DashboardPage />);

    const skeletons = container.querySelectorAll('[class*="skeleton"]');
    expect(skeletons.length).toBe(6);
  });

  it("renders user email in sidebar", () => {
    render(<DashboardPage />);

    expect(screen.getByText("user@example.com")).toBeInTheDocument();
  });

  it("does not navigate to article page on click (uses reader panel instead)", async () => {
    const user = userEvent.setup();
    render(<DashboardPage />);

    await user.click(screen.getByText("First Article"));

    expect(mockNavigate).not.toHaveBeenCalledWith(
      expect.stringContaining("/app/articles/"),
    );
  });

  it("renders sidebar toggle button", () => {
    render(<DashboardPage />);

    expect(
      screen.getByRole("button", { name: /collapse sidebar|expand sidebar/i }),
    ).toBeInTheDocument();
  });

  it("toggles sidebar collapsed state when toggle is clicked", async () => {
    const user = userEvent.setup();
    const { container } = render(<DashboardPage />);

    const sidebar = container.querySelector("aside");
    expect(sidebar?.className).not.toMatch(/sidebarCollapsed/);

    await user.click(screen.getByRole("button", { name: /collapse sidebar/i }));

    expect(sidebar?.className).toMatch(/sidebarCollapsed/);
  });
});
