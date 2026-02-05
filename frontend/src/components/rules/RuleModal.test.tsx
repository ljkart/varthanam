import { describe, it, expect, vi } from "vitest";
import { render, screen } from "../../test/utils";
import userEvent from "@testing-library/user-event";
import { RuleModal } from "./RuleModal";
import type { Rule } from "../../lib/rulesApi";
import type { Collection } from "../../lib/collectionsApi";

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
    description: "Science articles",
    user_id: 1,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
];

const mockRule: Rule = {
  id: 1,
  name: "AI News",
  include_keywords: "artificial intelligence,machine learning",
  exclude_keywords: "crypto",
  collection_id: 1,
  frequency_minutes: 60,
  last_run_at: null,
  is_active: true,
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
};

describe("RuleModal", () => {
  it("does not render when isOpen is false", () => {
    render(
      <RuleModal
        isOpen={false}
        onClose={() => {}}
        onSubmit={async () => {}}
        collections={mockCollections}
      />,
    );

    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("renders create form when isOpen is true", () => {
    render(
      <RuleModal
        isOpen={true}
        onClose={() => {}}
        onSubmit={async () => {}}
        collections={mockCollections}
      />,
    );

    expect(screen.getByRole("dialog")).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Create Rule" }),
    ).toBeInTheDocument();
  });

  it("renders edit form when rule is provided", () => {
    render(
      <RuleModal
        isOpen={true}
        onClose={() => {}}
        onSubmit={async () => {}}
        rule={mockRule}
        collections={mockCollections}
      />,
    );

    expect(screen.getByText("Edit Rule")).toBeInTheDocument();
    expect(screen.getByDisplayValue("AI News")).toBeInTheDocument();
  });

  it("populates form with rule data when editing", () => {
    render(
      <RuleModal
        isOpen={true}
        onClose={() => {}}
        onSubmit={async () => {}}
        rule={mockRule}
        collections={mockCollections}
      />,
    );

    expect(screen.getByDisplayValue("AI News")).toBeInTheDocument();
    expect(
      screen.getByDisplayValue("artificial intelligence,machine learning"),
    ).toBeInTheDocument();
    expect(screen.getByDisplayValue("crypto")).toBeInTheDocument();
  });

  it("calls onClose when close button is clicked", async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();

    render(
      <RuleModal
        isOpen={true}
        onClose={onClose}
        onSubmit={async () => {}}
        collections={mockCollections}
      />,
    );

    await user.click(screen.getByRole("button", { name: /close/i }));

    expect(onClose).toHaveBeenCalled();
  });

  it("calls onClose when Cancel button is clicked", async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();

    render(
      <RuleModal
        isOpen={true}
        onClose={onClose}
        onSubmit={async () => {}}
        collections={mockCollections}
      />,
    );

    await user.click(screen.getByRole("button", { name: /cancel/i }));

    expect(onClose).toHaveBeenCalled();
  });

  it("calls onClose when clicking overlay", async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();

    render(
      <RuleModal
        isOpen={true}
        onClose={onClose}
        onSubmit={async () => {}}
        collections={mockCollections}
      />,
    );

    // Click on the overlay (the dialog element itself)
    await user.click(screen.getByRole("dialog"));

    expect(onClose).toHaveBeenCalled();
  });

  it("disables submit button when name is empty", () => {
    render(
      <RuleModal
        isOpen={true}
        onClose={() => {}}
        onSubmit={async () => {}}
        collections={mockCollections}
      />,
    );

    expect(screen.getByRole("button", { name: /create rule/i })).toBeDisabled();
  });

  it("enables submit button when form is valid", async () => {
    const user = userEvent.setup();

    render(
      <RuleModal
        isOpen={true}
        onClose={() => {}}
        onSubmit={async () => {}}
        collections={mockCollections}
      />,
    );

    await user.type(screen.getByLabelText(/rule name/i), "Test Rule");

    expect(
      screen.getByRole("button", { name: /create rule/i }),
    ).not.toBeDisabled();
  });

  it("calls onSubmit with form data when submitted", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();

    render(
      <RuleModal
        isOpen={true}
        onClose={() => {}}
        onSubmit={onSubmit}
        collections={mockCollections}
      />,
    );

    await user.type(screen.getByLabelText(/rule name/i), "My Rule");
    await user.type(screen.getByLabelText(/include keywords/i), "tech,news");
    await user.type(screen.getByLabelText(/exclude keywords/i), "spam");
    await user.click(screen.getByRole("button", { name: /create rule/i }));

    expect(onSubmit).toHaveBeenCalledWith({
      name: "My Rule",
      frequency_minutes: 60,
      include_keywords: "tech,news",
      exclude_keywords: "spam",
      collection_id: null,
      is_active: true,
    });
  });

  it("allows selecting a collection", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();

    render(
      <RuleModal
        isOpen={true}
        onClose={() => {}}
        onSubmit={onSubmit}
        collections={mockCollections}
      />,
    );

    await user.type(screen.getByLabelText(/rule name/i), "My Rule");
    await user.selectOptions(
      screen.getByLabelText(/collection scope/i),
      "Tech News",
    );
    await user.click(screen.getByRole("button", { name: /create rule/i }));

    expect(onSubmit).toHaveBeenCalledWith(
      expect.objectContaining({
        collection_id: 1,
      }),
    );
  });

  it("allows toggling active state", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();

    render(
      <RuleModal
        isOpen={true}
        onClose={() => {}}
        onSubmit={onSubmit}
        collections={mockCollections}
      />,
    );

    await user.type(screen.getByLabelText(/rule name/i), "My Rule");
    await user.click(screen.getByRole("switch"));
    await user.click(screen.getByRole("button", { name: /create rule/i }));

    expect(onSubmit).toHaveBeenCalledWith(
      expect.objectContaining({
        is_active: false,
      }),
    );
  });

  it("allows selecting frequency", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();

    render(
      <RuleModal
        isOpen={true}
        onClose={() => {}}
        onSubmit={onSubmit}
        collections={mockCollections}
      />,
    );

    await user.type(screen.getByLabelText(/rule name/i), "My Rule");
    await user.selectOptions(
      screen.getByLabelText(/check frequency/i),
      "Every 30 minutes",
    );
    await user.click(screen.getByRole("button", { name: /create rule/i }));

    expect(onSubmit).toHaveBeenCalledWith(
      expect.objectContaining({
        frequency_minutes: 30,
      }),
    );
  });

  it("shows loading state on submit button", () => {
    render(
      <RuleModal
        isOpen={true}
        onClose={() => {}}
        onSubmit={async () => {}}
        rule={mockRule}
        collections={mockCollections}
        isLoading={true}
      />,
    );

    // When loading, the submit button is disabled (text may be hidden by spinner)
    const buttons = screen.getAllByRole("button");
    const submitButton = buttons.find(
      (btn) => btn.getAttribute("type") === "submit",
    );
    expect(submitButton).toBeDisabled();
  });

  it("displays error message when provided", () => {
    render(
      <RuleModal
        isOpen={true}
        onClose={() => {}}
        onSubmit={async () => {}}
        collections={mockCollections}
        error="Something went wrong"
      />,
    );

    expect(screen.getByText("Something went wrong")).toBeInTheDocument();
  });

  it("resets form when reopened", async () => {
    const user = userEvent.setup();

    const { rerender } = render(
      <RuleModal
        isOpen={true}
        onClose={() => {}}
        onSubmit={async () => {}}
        collections={mockCollections}
      />,
    );

    // Type in the form
    await user.type(screen.getByLabelText(/rule name/i), "Test Rule");
    expect(screen.getByDisplayValue("Test Rule")).toBeInTheDocument();

    // Close the modal
    rerender(
      <RuleModal
        isOpen={false}
        onClose={() => {}}
        onSubmit={async () => {}}
        collections={mockCollections}
      />,
    );

    // Reopen the modal
    rerender(
      <RuleModal
        isOpen={true}
        onClose={() => {}}
        onSubmit={async () => {}}
        collections={mockCollections}
      />,
    );

    // Form should be reset
    expect(screen.queryByDisplayValue("Test Rule")).not.toBeInTheDocument();
  });
});
