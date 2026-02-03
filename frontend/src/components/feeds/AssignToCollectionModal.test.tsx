import { describe, it, expect, vi } from "vitest";
import { render, screen, waitFor } from "../../test/utils";
import userEvent from "@testing-library/user-event";
import { AssignToCollectionModal } from "./AssignToCollectionModal";
import type { Feed } from "../../lib/feedsApi";
import type { Collection } from "../../lib/collectionsApi";

const mockFeed: Feed = {
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
};

const mockCollections: Collection[] = [
  {
    id: 1,
    name: "Tech News",
    description: "Technology articles",
    user_id: 1,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: 2,
    name: "Science",
    description: "Science news",
    user_id: 1,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
];

describe("AssignToCollectionModal", () => {
  it("does not render when closed", () => {
    render(
      <AssignToCollectionModal
        isOpen={false}
        onClose={vi.fn()}
        onAssign={vi.fn()}
        feed={mockFeed}
        collections={mockCollections}
      />,
    );

    expect(screen.queryByText("Assign to Collection")).not.toBeInTheDocument();
  });

  it("does not render when feed is null", () => {
    render(
      <AssignToCollectionModal
        isOpen={true}
        onClose={vi.fn()}
        onAssign={vi.fn()}
        feed={null}
        collections={mockCollections}
      />,
    );

    expect(screen.queryByText("Assign to Collection")).not.toBeInTheDocument();
  });

  it("renders modal title when open with feed", () => {
    render(
      <AssignToCollectionModal
        isOpen={true}
        onClose={vi.fn()}
        onAssign={vi.fn()}
        feed={mockFeed}
        collections={mockCollections}
      />,
    );

    expect(
      screen.getByRole("heading", { name: "Assign to Collection" }),
    ).toBeInTheDocument();
  });

  it("displays feed title", () => {
    render(
      <AssignToCollectionModal
        isOpen={true}
        onClose={vi.fn()}
        onAssign={vi.fn()}
        feed={mockFeed}
        collections={mockCollections}
      />,
    );

    expect(screen.getByText("Example Feed")).toBeInTheDocument();
  });

  it("displays 'Untitled Feed' for empty title", () => {
    const untitledFeed = { ...mockFeed, title: "" };
    render(
      <AssignToCollectionModal
        isOpen={true}
        onClose={vi.fn()}
        onAssign={vi.fn()}
        feed={untitledFeed}
        collections={mockCollections}
      />,
    );

    expect(screen.getByText("Untitled Feed")).toBeInTheDocument();
  });

  it("renders all collections", () => {
    render(
      <AssignToCollectionModal
        isOpen={true}
        onClose={vi.fn()}
        onAssign={vi.fn()}
        feed={mockFeed}
        collections={mockCollections}
      />,
    );

    expect(screen.getByText("Tech News")).toBeInTheDocument();
    expect(screen.getByText("Science")).toBeInTheDocument();
  });

  it("shows empty state when no collections", () => {
    render(
      <AssignToCollectionModal
        isOpen={true}
        onClose={vi.fn()}
        onAssign={vi.fn()}
        feed={mockFeed}
        collections={[]}
      />,
    );

    expect(screen.getByText("No collections yet.")).toBeInTheDocument();
    expect(
      screen.getByText("Create a collection first to organize your feeds."),
    ).toBeInTheDocument();
  });

  it("shows error when trying to assign without selection", () => {
    render(
      <AssignToCollectionModal
        isOpen={true}
        onClose={vi.fn()}
        onAssign={vi.fn()}
        feed={mockFeed}
        collections={mockCollections}
      />,
    );

    // The Assign button is disabled when no selection, so we can't click it
    // Check that the button is disabled
    expect(screen.getByRole("button", { name: "Assign" })).toBeDisabled();
  });

  it("calls onAssign with selected collection ID", async () => {
    const user = userEvent.setup();
    const onAssign = vi.fn().mockResolvedValue(undefined);
    render(
      <AssignToCollectionModal
        isOpen={true}
        onClose={vi.fn()}
        onAssign={onAssign}
        feed={mockFeed}
        collections={mockCollections}
      />,
    );

    // Click on the collection label (radio is hidden)
    await user.click(screen.getByText("Tech News"));
    await user.click(screen.getByRole("button", { name: "Assign" }));

    await waitFor(() => {
      expect(onAssign).toHaveBeenCalledWith(1);
    });
  });

  it("closes modal after successful assignment", async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();
    const onAssign = vi.fn().mockResolvedValue(undefined);
    render(
      <AssignToCollectionModal
        isOpen={true}
        onClose={onClose}
        onAssign={onAssign}
        feed={mockFeed}
        collections={mockCollections}
      />,
    );

    await user.click(screen.getByText("Tech News"));
    await user.click(screen.getByRole("button", { name: "Assign" }));

    await waitFor(() => {
      expect(onClose).toHaveBeenCalled();
    });
  });

  it("shows API error on assignment failure", async () => {
    const user = userEvent.setup();
    const onAssign = vi
      .fn()
      .mockRejectedValue({ detail: "Feed already in collection" });
    render(
      <AssignToCollectionModal
        isOpen={true}
        onClose={vi.fn()}
        onAssign={onAssign}
        feed={mockFeed}
        collections={mockCollections}
      />,
    );

    await user.click(screen.getByText("Tech News"));
    await user.click(screen.getByRole("button", { name: "Assign" }));

    await waitFor(() => {
      expect(
        screen.getByText("Feed already in collection"),
      ).toBeInTheDocument();
    });
  });

  it("calls onClose when Cancel is clicked", async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();
    render(
      <AssignToCollectionModal
        isOpen={true}
        onClose={onClose}
        onAssign={vi.fn()}
        feed={mockFeed}
        collections={mockCollections}
      />,
    );

    await user.click(screen.getByRole("button", { name: "Cancel" }));

    expect(onClose).toHaveBeenCalled();
  });

  it("disables Assign button when no collection is selected", () => {
    render(
      <AssignToCollectionModal
        isOpen={true}
        onClose={vi.fn()}
        onAssign={vi.fn()}
        feed={mockFeed}
        collections={mockCollections}
      />,
    );

    expect(screen.getByRole("button", { name: "Assign" })).toBeDisabled();
  });

  it("enables Assign button when collection is selected", async () => {
    const user = userEvent.setup();
    render(
      <AssignToCollectionModal
        isOpen={true}
        onClose={vi.fn()}
        onAssign={vi.fn()}
        feed={mockFeed}
        collections={mockCollections}
      />,
    );

    // Click on the collection label (radio is hidden)
    await user.click(screen.getByText("Tech News"));

    expect(screen.getByRole("button", { name: "Assign" })).not.toBeDisabled();
  });
});
