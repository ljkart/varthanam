import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "../test/utils";
import userEvent from "@testing-library/user-event";
import { LoginPage } from "./Login";

// Mock the API module
vi.mock("../lib/api", () => ({
  api: {
    login: vi.fn(),
    getCurrentUser: vi.fn(),
  },
}));

// Mock useNavigate
const mockNavigate = vi.fn();
vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

import { api } from "../lib/api";

describe("LoginPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  it("renders login form with all elements", () => {
    render(<LoginPage />);

    expect(screen.getByText("Welcome back")).toBeInTheDocument();
    expect(
      screen.getByText("Sign in to your account to continue reading"),
    ).toBeInTheDocument();
    expect(screen.getByLabelText("Email")).toBeInTheDocument();
    expect(screen.getByLabelText("Password")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /sign in/i }),
    ).toBeInTheDocument();
    expect(screen.getByText(/forgot password/i)).toBeInTheDocument();
    expect(screen.getByText(/don't have an account/i)).toBeInTheDocument();
  });

  it("renders logo", () => {
    render(<LoginPage />);
    expect(screen.getByText("VARTHANAM")).toBeInTheDocument();
  });

  it("allows user to type in email and password fields", async () => {
    const user = userEvent.setup();
    render(<LoginPage />);

    const emailInput = screen.getByLabelText("Email");
    const passwordInput = screen.getByLabelText("Password");

    await user.type(emailInput, "test@example.com");
    await user.type(passwordInput, "password123");

    expect(emailInput).toHaveValue("test@example.com");
    expect(passwordInput).toHaveValue("password123");
  });

  it("submits form with correct credentials and navigates on success", async () => {
    const user = userEvent.setup();
    vi.mocked(api.login).mockResolvedValueOnce({
      access_token: "test-token",
      token_type: "bearer",
    });

    render(<LoginPage />);

    await user.type(screen.getByLabelText("Email"), "user@example.com");
    await user.type(screen.getByLabelText("Password"), "secure-password");
    await user.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() => {
      expect(api.login).toHaveBeenCalledWith({
        email: "user@example.com",
        password: "secure-password",
      });
    });

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith("/app");
    });
  });

  it("displays error message on login failure", async () => {
    const user = userEvent.setup();
    vi.mocked(api.login).mockRejectedValueOnce({
      detail: "Invalid credentials",
      status: 401,
    });

    render(<LoginPage />);

    await user.type(screen.getByLabelText("Email"), "wrong@example.com");
    await user.type(screen.getByLabelText("Password"), "wrongpassword");
    await user.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() => {
      expect(screen.getByText("Invalid credentials")).toBeInTheDocument();
    });
  });

  it("disables submit button during loading", async () => {
    const user = userEvent.setup();
    // Make the login hang to test loading state
    vi.mocked(api.login).mockImplementationOnce(() => new Promise(() => {}));

    render(<LoginPage />);

    await user.type(screen.getByLabelText("Email"), "user@example.com");
    await user.type(screen.getByLabelText("Password"), "password");

    const submitButton = screen.getByRole("button", { name: /sign in/i });
    await user.click(submitButton);

    // Submit button should be disabled during loading
    await waitFor(() => {
      const buttons = screen.getAllByRole("button");
      const submitBtn = buttons.find(
        (btn) => btn.getAttribute("type") === "submit",
      );
      expect(submitBtn).toBeDisabled();
    });
  });

  it("has link to register page", () => {
    render(<LoginPage />);
    const signUpLink = screen.getByRole("link", { name: /sign up/i });
    expect(signUpLink).toHaveAttribute("href", "/register");
  });

  it("has link to forgot password", () => {
    render(<LoginPage />);
    const forgotLink = screen.getByRole("link", { name: /forgot password/i });
    expect(forgotLink).toHaveAttribute("href", "/forgot-password");
  });

  it("renders Google sign-in button", () => {
    render(<LoginPage />);
    expect(
      screen.getByRole("button", { name: /continue with google/i }),
    ).toBeInTheDocument();
  });

  it("renders remember me checkbox", () => {
    render(<LoginPage />);
    expect(screen.getByLabelText(/remember me/i)).toBeInTheDocument();
  });

  it("allows toggling remember me checkbox", async () => {
    const user = userEvent.setup();
    render(<LoginPage />);

    const checkbox = screen.getByRole("checkbox");
    expect(checkbox).not.toBeChecked();

    await user.click(checkbox);
    expect(checkbox).toBeChecked();

    await user.click(checkbox);
    expect(checkbox).not.toBeChecked();
  });
});
