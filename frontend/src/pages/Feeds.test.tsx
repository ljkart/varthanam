import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "../test/utils";
import userEvent from "@testing-library/user-event";
import { FeedsPage } from "./Feeds";
import { useFeeds } from "../hooks/useFeeds";
import { useCollections } from "../hooks/useCollections";
import { collectionFeedsApi } from "../lib/collectionFeedsApi";
import type { Feed } from "../lib/feedsApi";
import type { Collection } from "../lib/collectionsApi";

// Mock the hooks and API
vi.mock("../hooks/useFeeds");
vi.mock("../hooks/useCollections");
vi.mock("../lib/collectionFeedsApi");

const mockFeeds: Feed[] = [
  {
    id: 1,
    url: "https://example.com/rss",
    title: "Example Feed",
    description: "A test feed",
    site_url: "https://example.com",
    last_fetched_at: new Date().toISOString(),
    failure_count: 0,
    user_id: 1,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
];

const mockCollections: Collection[] = [
  {
    id: 1,
    name: "Tech News",
    description: "Technology articles",
    user_id: 1,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
];

describe("FeedsPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();

    // Default mock implementations
    vi.mocked(useFeeds).mockReturnValue({
      feeds: [],
      isLoading: false,
      error: null,
      addFeed: vi.fn().mockResolvedValue(mockFeeds[0]),
      clearError: vi.fn(),
    });

    vi.mocked(useCollections).mockReturnValue({
      collections: mockCollections,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
      createCollection: vi.fn(),
      updateCollection: vi.fn(),
      deleteCollection: vi.fn(),
    });

    vi.mocked(collectionFeedsApi.assign).mockResolvedValue({
      collection_id: 1,
      feed_id: 1,
      created_at: new Date().toISOString(),
    });
  });

  it("renders page title", () => {
    render(<FeedsPage />);

    expect(
      screen.getByRole("heading", { name: "Manage Feeds" }),
    ).toBeInTheDocument();
  });

  it("renders feed count in subtitle", () => {
    vi.mocked(useFeeds).mockReturnValue({
      feeds: mockFeeds,
      isLoading: false,
      error: null,
      addFeed: vi.fn(),
      clearError: vi.fn(),
    });

    render(<FeedsPage />);

    expect(screen.getByText("1 feed connected")).toBeInTheDocument();
  });

  it("renders plural feed count", () => {
    vi.mocked(useFeeds).mockReturnValue({
      feeds: [...mockFeeds, { ...mockFeeds[0], id: 2 }],
      isLoading: false,
      error: null,
      addFeed: vi.fn(),
      clearError: vi.fn(),
    });

    render(<FeedsPage />);

    expect(screen.getByText("2 feeds connected")).toBeInTheDocument();
  });

  it("renders Add Feed button", () => {
    render(<FeedsPage />);

    // Button text is "Add Feed" but has an icon, check for text content
    expect(screen.getAllByText("Add Feed").length).toBeGreaterThan(0);
  });

  it("shows loading skeleton when loading", () => {
    vi.mocked(useFeeds).mockReturnValue({
      feeds: [],
      isLoading: true,
      error: null,
      addFeed: vi.fn(),
      clearError: vi.fn(),
    });

    render(<FeedsPage />);

    expect(screen.getByText("FEED NAME")).toBeInTheDocument();
    expect(screen.getByText("URL")).toBeInTheDocument();
    expect(screen.getByText("LAST FETCHED")).toBeInTheDocument();
    expect(screen.getByText("STATUS")).toBeInTheDocument();
    expect(screen.getByText("ACTIONS")).toBeInTheDocument();
  });

  it("shows empty state when no feeds", () => {
    render(<FeedsPage />);

    expect(
      screen.getByRole("heading", { name: "No feeds yet" }),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Add your first RSS feed to start aggregating content."),
    ).toBeInTheDocument();
  });

  it("renders feeds table when feeds exist", () => {
    vi.mocked(useFeeds).mockReturnValue({
      feeds: mockFeeds,
      isLoading: false,
      error: null,
      addFeed: vi.fn(),
      clearError: vi.fn(),
    });

    render(<FeedsPage />);

    expect(screen.getByText("Example Feed")).toBeInTheDocument();
    expect(screen.getByText("Active")).toBeInTheDocument();
  });

  it("opens Add Feed modal when button is clicked", async () => {
    const user = userEvent.setup();
    render(<FeedsPage />);

    // Click the first Add Feed button (in the header)
    const addFeedButtons = screen.getAllByText("Add Feed");
    await user.click(addFeedButtons[0]);

    expect(
      screen.getByRole("heading", { name: "Add Feed" }),
    ).toBeInTheDocument();
  });

  it("opens Add Feed modal from empty state button", async () => {
    const user = userEvent.setup();
    render(<FeedsPage />);

    // Click the Add Feed button in the empty state
    const buttons = screen.getAllByRole("button", { name: /add feed/i });
    await user.click(buttons[1]); // The second one is in empty state

    expect(
      screen.getByRole("heading", { name: "Add Feed" }),
    ).toBeInTheDocument();
  });

  it("shows success message after adding feed", async () => {
    const user = userEvent.setup();
    const addFeed = vi.fn().mockResolvedValue(mockFeeds[0]);

    vi.mocked(useFeeds).mockReturnValue({
      feeds: [],
      isLoading: false,
      error: null,
      addFeed,
      clearError: vi.fn(),
    });

    render(<FeedsPage />);

    // Open the Add Feed modal
    const addFeedButtons = screen.getAllByText("Add Feed");
    await user.click(addFeedButtons[0]);

    await user.type(
      screen.getByLabelText("Feed URL"),
      "https://example.com/rss",
    );

    // Click the submit button in the modal (which says "Add Feed")
    const modalButtons = screen.getAllByText("Add Feed");
    const submitButton = modalButtons.find(
      (btn) => btn.closest("button")?.getAttribute("type") === "submit",
    );
    await user.click(submitButton!);

    await waitFor(() => {
      expect(
        screen.getByText(/Added "Example Feed" successfully/),
      ).toBeInTheDocument();
    });
  });

  it("opens Assign to Collection modal when assign button is clicked", async () => {
    const user = userEvent.setup();

    vi.mocked(useFeeds).mockReturnValue({
      feeds: mockFeeds,
      isLoading: false,
      error: null,
      addFeed: vi.fn(),
      clearError: vi.fn(),
    });

    render(<FeedsPage />);

    const assignButton = screen.getByRole("button", {
      name: /assign example feed to collection/i,
    });
    await user.click(assignButton);

    expect(
      screen.getByRole("heading", { name: "Assign to Collection" }),
    ).toBeInTheDocument();
  });

  it("shows success message after assigning to collection", async () => {
    const user = userEvent.setup();

    vi.mocked(useFeeds).mockReturnValue({
      feeds: mockFeeds,
      isLoading: false,
      error: null,
      addFeed: vi.fn(),
      clearError: vi.fn(),
    });

    render(<FeedsPage />);

    // Open assign modal
    const assignButton = screen.getByRole("button", {
      name: /assign example feed to collection/i,
    });
    await user.click(assignButton);

    // Select collection by clicking on the label text (radio is hidden)
    await user.click(screen.getByText("Tech News"));
    await user.click(screen.getByRole("button", { name: "Assign" }));

    await waitFor(() => {
      expect(
        screen.getByText(/Assigned "Example Feed" to "Tech News"/),
      ).toBeInTheDocument();
    });
  });

  it("calls collectionFeedsApi.assign with correct IDs", async () => {
    const user = userEvent.setup();

    vi.mocked(useFeeds).mockReturnValue({
      feeds: mockFeeds,
      isLoading: false,
      error: null,
      addFeed: vi.fn(),
      clearError: vi.fn(),
    });

    render(<FeedsPage />);

    // Open assign modal
    const assignButton = screen.getByRole("button", {
      name: /assign example feed to collection/i,
    });
    await user.click(assignButton);

    // Select collection by clicking on the label text (radio is hidden)
    await user.click(screen.getByText("Tech News"));
    await user.click(screen.getByRole("button", { name: "Assign" }));

    await waitFor(() => {
      expect(collectionFeedsApi.assign).toHaveBeenCalledWith(1, 1);
    });
  });

  it("renders table headers correctly", () => {
    vi.mocked(useFeeds).mockReturnValue({
      feeds: mockFeeds,
      isLoading: false,
      error: null,
      addFeed: vi.fn(),
      clearError: vi.fn(),
    });

    render(<FeedsPage />);

    expect(screen.getByText("FEED NAME")).toBeInTheDocument();
    expect(screen.getByText("URL")).toBeInTheDocument();
    expect(screen.getByText("LAST FETCHED")).toBeInTheDocument();
    expect(screen.getByText("STATUS")).toBeInTheDocument();
    expect(screen.getByText("ACTIONS")).toBeInTheDocument();
  });
});
