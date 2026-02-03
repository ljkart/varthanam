import { describe, it, expect, vi } from "vitest";
import { render, screen } from "../../test/utils";
import userEvent from "@testing-library/user-event";
import { CollectionCard } from "./CollectionCard";

const mockCollection = {
  id: 1,
  name: "Tech News",
  description: "Technology articles and updates",
  user_id: 1,
  created_at: "2024-01-01T00:00:00Z",
  updated_at: "2024-01-01T00:00:00Z",
};

describe("CollectionCard", () => {
  it("renders collection name", () => {
    render(
      <CollectionCard
        collection={mockCollection}
        onEdit={vi.fn()}
        onDelete={vi.fn()}
      />,
    );

    expect(screen.getByText("Tech News")).toBeInTheDocument();
  });

  it("renders collection description", () => {
    render(
      <CollectionCard
        collection={mockCollection}
        onEdit={vi.fn()}
        onDelete={vi.fn()}
      />,
    );

    expect(
      screen.getByText("Technology articles and updates"),
    ).toBeInTheDocument();
  });

  it("does not render description when null", () => {
    const collectionWithoutDesc = { ...mockCollection, description: null };
    render(
      <CollectionCard
        collection={collectionWithoutDesc}
        onEdit={vi.fn()}
        onDelete={vi.fn()}
      />,
    );

    expect(screen.getByText("Tech News")).toBeInTheDocument();
    expect(
      screen.queryByText("Technology articles and updates"),
    ).not.toBeInTheDocument();
  });

  it("calls onEdit when edit button clicked", async () => {
    const mockOnEdit = vi.fn();
    const user = userEvent.setup();

    render(
      <CollectionCard
        collection={mockCollection}
        onEdit={mockOnEdit}
        onDelete={vi.fn()}
      />,
    );

    await user.click(screen.getByLabelText("Edit Tech News"));
    expect(mockOnEdit).toHaveBeenCalledWith(mockCollection);
  });

  it("calls onDelete when delete button clicked", async () => {
    const mockOnDelete = vi.fn();
    const user = userEvent.setup();

    render(
      <CollectionCard
        collection={mockCollection}
        onEdit={vi.fn()}
        onDelete={mockOnDelete}
      />,
    );

    await user.click(screen.getByLabelText("Delete Tech News"));
    expect(mockOnDelete).toHaveBeenCalledWith(mockCollection);
  });

  it("has accessible button labels", () => {
    render(
      <CollectionCard
        collection={mockCollection}
        onEdit={vi.fn()}
        onDelete={vi.fn()}
      />,
    );

    expect(screen.getByLabelText("Edit Tech News")).toBeInTheDocument();
    expect(screen.getByLabelText("Delete Tech News")).toBeInTheDocument();
  });
});
