import { describe, it, expect, vi } from "vitest";
import { render, screen, waitFor } from "../../test/utils";
import userEvent from "@testing-library/user-event";
import { AddFeedModal } from "./AddFeedModal";

describe("AddFeedModal", () => {
  it("does not render when closed", () => {
    render(
      <AddFeedModal isOpen={false} onClose={vi.fn()} onSubmit={vi.fn()} />,
    );

    expect(screen.queryByText("Add Feed")).not.toBeInTheDocument();
  });

  it("renders modal title when open", () => {
    render(<AddFeedModal isOpen={true} onClose={vi.fn()} onSubmit={vi.fn()} />);

    expect(
      screen.getByRole("heading", { name: "Add Feed" }),
    ).toBeInTheDocument();
  });

  it("renders URL input field", () => {
    render(<AddFeedModal isOpen={true} onClose={vi.fn()} onSubmit={vi.fn()} />);

    expect(screen.getByLabelText("Feed URL")).toBeInTheDocument();
    expect(
      screen.getByPlaceholderText("https://example.com/rss"),
    ).toBeInTheDocument();
  });

  it("renders Cancel and Add Feed buttons", () => {
    render(<AddFeedModal isOpen={true} onClose={vi.fn()} onSubmit={vi.fn()} />);

    expect(screen.getByRole("button", { name: "Cancel" })).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Add Feed" }),
    ).toBeInTheDocument();
  });

  it("shows error for empty URL on submit", async () => {
    const user = userEvent.setup();
    render(<AddFeedModal isOpen={true} onClose={vi.fn()} onSubmit={vi.fn()} />);

    await user.click(screen.getByRole("button", { name: "Add Feed" }));

    expect(screen.getByText("Feed URL is required")).toBeInTheDocument();
  });

  it("shows error for invalid URL", async () => {
    const user = userEvent.setup();
    render(<AddFeedModal isOpen={true} onClose={vi.fn()} onSubmit={vi.fn()} />);

    // Use a string that passes browser URL validation but fails our custom check
    await user.type(screen.getByLabelText("Feed URL"), "javascript:alert(1)");
    await user.click(screen.getByRole("button", { name: "Add Feed" }));

    expect(
      screen.getByText("URL must start with http:// or https://"),
    ).toBeInTheDocument();
  });

  it("shows error for non-http URL", async () => {
    const user = userEvent.setup();
    render(<AddFeedModal isOpen={true} onClose={vi.fn()} onSubmit={vi.fn()} />);

    await user.type(
      screen.getByLabelText("Feed URL"),
      "ftp://example.com/feed",
    );
    await user.click(screen.getByRole("button", { name: "Add Feed" }));

    expect(
      screen.getByText("URL must start with http:// or https://"),
    ).toBeInTheDocument();
  });

  it("calls onSubmit with valid URL", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    render(
      <AddFeedModal isOpen={true} onClose={vi.fn()} onSubmit={onSubmit} />,
    );

    await user.type(
      screen.getByLabelText("Feed URL"),
      "https://example.com/rss",
    );
    await user.click(screen.getByRole("button", { name: "Add Feed" }));

    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledWith("https://example.com/rss");
    });
  });

  it("calls onClose when Cancel is clicked", async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();
    render(<AddFeedModal isOpen={true} onClose={onClose} onSubmit={vi.fn()} />);

    await user.click(screen.getByRole("button", { name: "Cancel" }));

    expect(onClose).toHaveBeenCalled();
  });

  it("closes modal after successful submit", async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    render(
      <AddFeedModal isOpen={true} onClose={onClose} onSubmit={onSubmit} />,
    );

    await user.type(
      screen.getByLabelText("Feed URL"),
      "https://example.com/rss",
    );
    await user.click(screen.getByRole("button", { name: "Add Feed" }));

    await waitFor(() => {
      expect(onClose).toHaveBeenCalled();
    });
  });

  it("shows API error on submit failure", async () => {
    const user = userEvent.setup();
    const onSubmit = vi
      .fn()
      .mockRejectedValue({ detail: "Feed already exists" });
    render(
      <AddFeedModal isOpen={true} onClose={vi.fn()} onSubmit={onSubmit} />,
    );

    await user.type(
      screen.getByLabelText("Feed URL"),
      "https://example.com/rss",
    );
    await user.click(screen.getByRole("button", { name: "Add Feed" }));

    await waitFor(() => {
      expect(screen.getByText("Feed already exists")).toBeInTheDocument();
    });
  });

  it("shows loading state when isLoading is true", () => {
    render(
      <AddFeedModal
        isOpen={true}
        onClose={vi.fn()}
        onSubmit={vi.fn()}
        isLoading={true}
      />,
    );

    // When loading, the button shows a spinner and is disabled
    // Find the submit button which is in the footer
    const buttons = screen.getAllByRole("button");
    const submitButton = buttons.find(
      (btn) => btn.getAttribute("type") === "submit",
    );
    expect(submitButton).toBeDisabled();
  });

  it("renders hint text", () => {
    render(<AddFeedModal isOpen={true} onClose={vi.fn()} onSubmit={vi.fn()} />);

    expect(
      screen.getByText(/Enter the URL of an RSS or Atom feed/),
    ).toBeInTheDocument();
  });
});
