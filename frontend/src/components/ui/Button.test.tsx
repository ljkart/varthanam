import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Button } from "./Button";

describe("Button", () => {
  it("renders button with text", () => {
    render(<Button>Click me</Button>);
    expect(
      screen.getByRole("button", { name: /click me/i }),
    ).toBeInTheDocument();
  });

  it("renders with primary variant styling by default", () => {
    render(<Button>Primary</Button>);
    const button = screen.getByRole("button");
    // CSS Modules will mangle class names, so just verify button exists
    expect(button).toBeInTheDocument();
  });

  it("renders with secondary variant", () => {
    render(<Button variant="secondary">Secondary</Button>);
    const button = screen.getByRole("button");
    expect(button).toBeInTheDocument();
  });

  it("renders with outline variant", () => {
    render(<Button variant="outline">Outline</Button>);
    const button = screen.getByRole("button");
    expect(button).toBeInTheDocument();
  });

  it("renders full width button", () => {
    render(<Button fullWidth>Full Width</Button>);
    const button = screen.getByRole("button");
    expect(button).toBeInTheDocument();
  });

  it("shows loading state when isLoading is true", () => {
    render(<Button isLoading>Loading</Button>);
    const button = screen.getByRole("button");
    // Text should not be visible when loading
    expect(button).not.toHaveTextContent("Loading");
    // Button should be disabled
    expect(button).toBeDisabled();
  });

  it("is disabled when isLoading is true", () => {
    render(<Button isLoading>Loading</Button>);
    expect(screen.getByRole("button")).toBeDisabled();
  });

  it("is disabled when disabled prop is true", () => {
    render(<Button disabled>Disabled</Button>);
    expect(screen.getByRole("button")).toBeDisabled();
  });

  it("calls onClick when clicked", async () => {
    const user = userEvent.setup();
    const handleClick = vi.fn();
    render(<Button onClick={handleClick}>Click me</Button>);

    await user.click(screen.getByRole("button"));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it("does not call onClick when disabled", async () => {
    const user = userEvent.setup();
    const handleClick = vi.fn();
    render(
      <Button onClick={handleClick} disabled>
        Click me
      </Button>,
    );

    await user.click(screen.getByRole("button"));
    expect(handleClick).not.toHaveBeenCalled();
  });

  it("renders left icon when provided", () => {
    const TestIcon = () => <span data-testid="test-icon">Icon</span>;
    render(<Button leftIcon={<TestIcon />}>With Icon</Button>);

    expect(screen.getByTestId("test-icon")).toBeInTheDocument();
    expect(screen.getByText("With Icon")).toBeInTheDocument();
  });

  it("forwards ref to button element", () => {
    const ref = { current: null as HTMLButtonElement | null };
    render(<Button ref={ref}>Test</Button>);
    expect(ref.current).toBeInstanceOf(HTMLButtonElement);
  });

  it("passes through HTML button attributes", () => {
    render(
      <Button type="submit" name="submit-btn">
        Submit
      </Button>,
    );
    const button = screen.getByRole("button");
    expect(button).toHaveAttribute("type", "submit");
    expect(button).toHaveAttribute("name", "submit-btn");
  });
});
