import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "../../test/utils";
import userEvent from "@testing-library/user-event";
import { CollectionModal } from "./CollectionModal";

describe("CollectionModal", () => {
  const mockOnClose = vi.fn();
  const mockOnSubmit = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders create modal when no collection provided", () => {
    render(
      <CollectionModal
        isOpen={true}
        onClose={mockOnClose}
        onSubmit={mockOnSubmit}
      />,
    );

    expect(
      screen.getByRole("heading", { name: "Create Collection" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /create collection/i }),
    ).toBeInTheDocument();
  });

  it("renders edit modal when collection provided", () => {
    const collection = {
      id: 1,
      name: "Tech News",
      description: "Technology articles",
      user_id: 1,
      created_at: "2024-01-01T00:00:00Z",
      updated_at: "2024-01-01T00:00:00Z",
    };

    render(
      <CollectionModal
        isOpen={true}
        onClose={mockOnClose}
        onSubmit={mockOnSubmit}
        collection={collection}
      />,
    );

    expect(screen.getByText("Edit Collection")).toBeInTheDocument();
    expect(screen.getByDisplayValue("Tech News")).toBeInTheDocument();
    expect(screen.getByDisplayValue("Technology articles")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /save changes/i }),
    ).toBeInTheDocument();
  });

  it("calls onClose when Cancel button clicked", async () => {
    const user = userEvent.setup();
    render(
      <CollectionModal
        isOpen={true}
        onClose={mockOnClose}
        onSubmit={mockOnSubmit}
      />,
    );

    await user.click(screen.getByRole("button", { name: /cancel/i }));
    expect(mockOnClose).toHaveBeenCalled();
  });

  it("calls onClose when close icon clicked", async () => {
    const user = userEvent.setup();
    render(
      <CollectionModal
        isOpen={true}
        onClose={mockOnClose}
        onSubmit={mockOnSubmit}
      />,
    );

    await user.click(screen.getByRole("button", { name: /close modal/i }));
    expect(mockOnClose).toHaveBeenCalled();
  });

  it("validates name is required", async () => {
    const user = userEvent.setup();
    render(
      <CollectionModal
        isOpen={true}
        onClose={mockOnClose}
        onSubmit={mockOnSubmit}
      />,
    );

    // Submit with empty name
    await user.click(
      screen.getByRole("button", { name: /create collection/i }),
    );

    await waitFor(() => {
      expect(
        screen.getByText("Collection name is required"),
      ).toBeInTheDocument();
    });
    expect(mockOnSubmit).not.toHaveBeenCalled();
  });

  it("submits with valid data", async () => {
    mockOnSubmit.mockResolvedValueOnce(undefined);
    const user = userEvent.setup();

    render(
      <CollectionModal
        isOpen={true}
        onClose={mockOnClose}
        onSubmit={mockOnSubmit}
      />,
    );

    await user.type(screen.getByLabelText(/collection name/i), "My Collection");
    await user.type(screen.getByLabelText(/description/i), "A description");
    await user.click(
      screen.getByRole("button", { name: /create collection/i }),
    );

    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledWith({
        name: "My Collection",
        description: "A description",
      });
    });
  });

  it("trims whitespace from inputs", async () => {
    mockOnSubmit.mockResolvedValueOnce(undefined);
    const user = userEvent.setup();

    render(
      <CollectionModal
        isOpen={true}
        onClose={mockOnClose}
        onSubmit={mockOnSubmit}
      />,
    );

    await user.type(
      screen.getByLabelText(/collection name/i),
      "  My Collection  ",
    );
    await user.click(
      screen.getByRole("button", { name: /create collection/i }),
    );

    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledWith({
        name: "My Collection",
        description: undefined,
      });
    });
  });

  it("shows error from API", async () => {
    mockOnSubmit.mockRejectedValueOnce({ detail: "Name already exists" });
    const user = userEvent.setup();

    render(
      <CollectionModal
        isOpen={true}
        onClose={mockOnClose}
        onSubmit={mockOnSubmit}
      />,
    );

    await user.type(screen.getByLabelText(/collection name/i), "Existing Name");
    await user.click(
      screen.getByRole("button", { name: /create collection/i }),
    );

    await waitFor(() => {
      expect(screen.getByText("Name already exists")).toBeInTheDocument();
    });
  });

  it("does not render when closed", () => {
    render(
      <CollectionModal
        isOpen={false}
        onClose={mockOnClose}
        onSubmit={mockOnSubmit}
      />,
    );

    expect(screen.queryByText("Create Collection")).not.toBeInTheDocument();
  });
});
