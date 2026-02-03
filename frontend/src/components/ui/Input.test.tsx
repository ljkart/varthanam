import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Input } from "./Input";

describe("Input", () => {
  it("renders input with label", () => {
    render(<Input label="Email" />);
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
  });

  it("renders input without label", () => {
    render(<Input placeholder="Enter text" />);
    expect(screen.getByPlaceholderText("Enter text")).toBeInTheDocument();
  });

  it("shows error message when error prop is provided", () => {
    render(<Input label="Email" error="Invalid email" />);
    expect(screen.getByText("Invalid email")).toBeInTheDocument();
    expect(screen.getByRole("alert")).toHaveTextContent("Invalid email");
  });

  it("sets aria-invalid when error is present", () => {
    render(<Input label="Email" error="Invalid email" />);
    const input = screen.getByLabelText(/email/i);
    expect(input).toHaveAttribute("aria-invalid", "true");
  });

  it("toggles password visibility", async () => {
    const user = userEvent.setup();
    render(<Input label="Password" type="password" />);

    const input = screen.getByLabelText("Password");
    expect(input).toHaveAttribute("type", "password");

    // Click the toggle button
    const toggleButton = screen.getByRole("button", { name: /show password/i });
    await user.click(toggleButton);

    expect(input).toHaveAttribute("type", "text");
    expect(
      screen.getByRole("button", { name: /hide password/i }),
    ).toBeInTheDocument();

    // Click again to hide
    await user.click(screen.getByRole("button", { name: /hide password/i }));
    expect(input).toHaveAttribute("type", "password");
  });

  it("forwards ref to input element", () => {
    const ref = { current: null as HTMLInputElement | null };
    render(<Input ref={ref} label="Test" />);
    expect(ref.current).toBeInstanceOf(HTMLInputElement);
  });

  it("passes through HTML input attributes", () => {
    render(
      <Input
        label="Email"
        type="email"
        required
        autoComplete="email"
        placeholder="test@example.com"
      />,
    );

    const input = screen.getByLabelText(/email/i);
    expect(input).toHaveAttribute("type", "email");
    expect(input).toBeRequired();
    expect(input).toHaveAttribute("autocomplete", "email");
    expect(input).toHaveAttribute("placeholder", "test@example.com");
  });

  it("associates label with input via htmlFor", () => {
    render(<Input label="Username" id="username-input" />);
    const label = screen.getByText("Username");
    expect(label).toHaveAttribute("for", "username-input");
  });
});
