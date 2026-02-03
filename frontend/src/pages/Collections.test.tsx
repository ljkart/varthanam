import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "../test/utils";
import userEvent from "@testing-library/user-event";
import { CollectionsPage } from "./Collections";

// Mock the useCollections hook
vi.mock("../hooks/useCollections", () => ({
  useCollections: vi.fn(),
}));

import { useCollections } from "../hooks/useCollections";

const mockCollections = [
  {
    id: 1,
    name: "Tech News",
    description: "Technology articles",
    user_id: 1,
    created_at: "2024-01-01T00:00:00Z",
    updated_at: "2024-01-01T00:00:00Z",
  },
  {
    id: 2,
    name: "AI & ML",
    description: null,
    user_id: 1,
    created_at: "2024-01-02T00:00:00Z",
    updated_at: "2024-01-02T00:00:00Z",
  },
];

describe("CollectionsPage", () => {
  const mockRefetch = vi.fn();
  const mockCreateCollection = vi.fn();
  const mockUpdateCollection = vi.fn();
  const mockDeleteCollection = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useCollections).mockReturnValue({
      collections: mockCollections,
      isLoading: false,
      error: null,
      refetch: mockRefetch,
      createCollection: mockCreateCollection,
      updateCollection: mockUpdateCollection,
      deleteCollection: mockDeleteCollection,
    });
  });

  it("renders page title", () => {
    render(<CollectionsPage />);
    expect(screen.getByText("Collections")).toBeInTheDocument();
  });

  it("renders collection list", () => {
    render(<CollectionsPage />);
    expect(screen.getByText("Tech News")).toBeInTheDocument();
    expect(screen.getByText("AI & ML")).toBeInTheDocument();
  });

  it("shows loading skeleton", () => {
    vi.mocked(useCollections).mockReturnValue({
      collections: [],
      isLoading: true,
      error: null,
      refetch: mockRefetch,
      createCollection: mockCreateCollection,
      updateCollection: mockUpdateCollection,
      deleteCollection: mockDeleteCollection,
    });

    render(<CollectionsPage />);
    expect(screen.getByText("Collections")).toBeInTheDocument();
  });

  it("shows error state with retry button", async () => {
    vi.mocked(useCollections).mockReturnValue({
      collections: [],
      isLoading: false,
      error: "Failed to load collections",
      refetch: mockRefetch,
      createCollection: mockCreateCollection,
      updateCollection: mockUpdateCollection,
      deleteCollection: mockDeleteCollection,
    });

    const user = userEvent.setup();
    render(<CollectionsPage />);

    expect(screen.getByText("Failed to load collections")).toBeInTheDocument();
    const retryButton = screen.getByRole("button", { name: /try again/i });
    await user.click(retryButton);
    expect(mockRefetch).toHaveBeenCalled();
  });

  it("shows empty state when no collections", () => {
    vi.mocked(useCollections).mockReturnValue({
      collections: [],
      isLoading: false,
      error: null,
      refetch: mockRefetch,
      createCollection: mockCreateCollection,
      updateCollection: mockUpdateCollection,
      deleteCollection: mockDeleteCollection,
    });

    render(<CollectionsPage />);
    expect(screen.getByText("No collections yet")).toBeInTheDocument();
    expect(
      screen.getByText(
        "Create your first collection to start organizing your feeds.",
      ),
    ).toBeInTheDocument();
  });

  it("opens create modal when clicking New Collection button", async () => {
    const user = userEvent.setup();
    render(<CollectionsPage />);

    const newButton = screen.getByRole("button", { name: /new collection/i });
    await user.click(newButton);

    expect(
      screen.getByRole("heading", { name: "Create Collection" }),
    ).toBeInTheDocument();
  });

  it("creates a new collection", async () => {
    mockCreateCollection.mockResolvedValueOnce({
      id: 3,
      name: "New Collection",
      description: "Test description",
      user_id: 1,
      created_at: "2024-01-03T00:00:00Z",
      updated_at: "2024-01-03T00:00:00Z",
    });

    const user = userEvent.setup();
    render(<CollectionsPage />);

    await user.click(screen.getByRole("button", { name: /new collection/i }));

    const nameInput = screen.getByLabelText(/collection name/i);
    await user.type(nameInput, "New Collection");

    const descInput = screen.getByLabelText(/description/i);
    await user.type(descInput, "Test description");

    const createButton = screen.getByRole("button", {
      name: /create collection/i,
    });
    await user.click(createButton);

    await waitFor(() => {
      expect(mockCreateCollection).toHaveBeenCalledWith({
        name: "New Collection",
        description: "Test description",
      });
    });
  });

  it("opens edit modal when clicking edit button", async () => {
    const user = userEvent.setup();
    render(<CollectionsPage />);

    const editButtons = screen.getAllByLabelText(/edit/i);
    await user.click(editButtons[0]);

    expect(screen.getByText("Edit Collection")).toBeInTheDocument();
    expect(screen.getByDisplayValue("Tech News")).toBeInTheDocument();
  });

  it("updates a collection", async () => {
    mockUpdateCollection.mockResolvedValueOnce({
      ...mockCollections[0],
      name: "Updated Name",
    });

    const user = userEvent.setup();
    render(<CollectionsPage />);

    const editButtons = screen.getAllByLabelText(/edit/i);
    await user.click(editButtons[0]);

    const nameInput = screen.getByDisplayValue("Tech News");
    await user.clear(nameInput);
    await user.type(nameInput, "Updated Name");

    const saveButton = screen.getByRole("button", { name: /save changes/i });
    await user.click(saveButton);

    await waitFor(() => {
      expect(mockUpdateCollection).toHaveBeenCalledWith(1, {
        name: "Updated Name",
        description: "Technology articles",
      });
    });
  });

  it("opens delete confirmation modal", async () => {
    const user = userEvent.setup();
    render(<CollectionsPage />);

    const deleteButtons = screen.getAllByLabelText(/delete/i);
    await user.click(deleteButtons[0]);

    expect(
      screen.getByRole("heading", { name: "Delete Collection" }),
    ).toBeInTheDocument();
    // Check that the modal contains the collection name
    expect(
      screen.getByText(/are you sure you want to delete/i),
    ).toBeInTheDocument();
  });

  it("deletes a collection", async () => {
    mockDeleteCollection.mockResolvedValueOnce(undefined);

    const user = userEvent.setup();
    render(<CollectionsPage />);

    const deleteButtons = screen.getAllByLabelText(/delete/i);
    await user.click(deleteButtons[0]);

    const confirmDeleteButton = screen.getByRole("button", {
      name: /^delete$/i,
    });
    await user.click(confirmDeleteButton);

    await waitFor(() => {
      expect(mockDeleteCollection).toHaveBeenCalledWith(1);
    });
  });

  it("validates required name field", async () => {
    const user = userEvent.setup();
    render(<CollectionsPage />);

    await user.click(screen.getByRole("button", { name: /new collection/i }));

    // Submit with empty name
    const createButton = screen.getByRole("button", {
      name: /create collection/i,
    });
    await user.click(createButton);

    await waitFor(() => {
      expect(
        screen.getByText("Collection name is required"),
      ).toBeInTheDocument();
    });

    expect(mockCreateCollection).not.toHaveBeenCalled();
  });
});
