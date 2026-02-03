import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "../test/utils";
import userEvent from "@testing-library/user-event";
import { RegisterPage } from "./Register";

// Mock the API module
vi.mock("../lib/api", () => ({
  api: {
    register: vi.fn(),
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

describe("RegisterPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  it("renders registration form with all elements", () => {
    render(<RegisterPage />);

    expect(screen.getByText("Create your account")).toBeInTheDocument();
    expect(
      screen.getByText("Start curating your personalized news feed"),
    ).toBeInTheDocument();
    expect(screen.getByLabelText("Email")).toBeInTheDocument();
    expect(screen.getByLabelText("Password")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /create account/i }),
    ).toBeInTheDocument();
  });

  it("renders logo", () => {
    render(<RegisterPage />);
    expect(screen.getByText("VARTHANAM")).toBeInTheDocument();
  });

  it("allows user to type in all fields", async () => {
    const user = userEvent.setup();
    render(<RegisterPage />);

    const emailInput = screen.getByLabelText("Email");
    const passwordInput = screen.getByLabelText("Password");

    await user.type(emailInput, "john@example.com");
    await user.type(passwordInput, "password123");

    expect(emailInput).toHaveValue("john@example.com");
    expect(passwordInput).toHaveValue("password123");
  });

  it("submits form and navigates to login on success", async () => {
    const user = userEvent.setup();
    vi.mocked(api.register).mockResolvedValueOnce({
      id: 1,
      email: "john@example.com",
      is_active: true,
      created_at: "2024-01-01T00:00:00Z",
    });

    render(<RegisterPage />);

    await user.type(screen.getByLabelText("Email"), "john@example.com");
    await user.type(screen.getByLabelText("Password"), "password123");
    await user.click(screen.getByRole("button", { name: /create account/i }));

    await waitFor(() => {
      expect(api.register).toHaveBeenCalledWith({
        email: "john@example.com",
        password: "password123",
      });
    });

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith("/login", {
        state: { registered: true },
      });
    });
  });

  it("displays error message on registration failure", async () => {
    const user = userEvent.setup();
    vi.mocked(api.register).mockRejectedValueOnce({
      detail: "Email already registered",
      status: 400,
    });

    render(<RegisterPage />);

    await user.type(screen.getByLabelText("Email"), "existing@example.com");
    await user.type(screen.getByLabelText("Password"), "password123");
    await user.click(screen.getByRole("button", { name: /create account/i }));

    await waitFor(() => {
      expect(screen.getByText("Email already registered")).toBeInTheDocument();
    });
  });

  it("validates password minimum length", async () => {
    const user = userEvent.setup();
    render(<RegisterPage />);

    await user.type(screen.getByLabelText("Email"), "john@example.com");
    await user.type(screen.getByLabelText("Password"), "short");
    await user.click(screen.getByRole("button", { name: /create account/i }));

    await waitFor(() => {
      expect(
        screen.getByText("Password must be at least 8 characters"),
      ).toBeInTheDocument();
    });

    // API should not be called
    expect(api.register).not.toHaveBeenCalled();
  });

  it("disables submit button during loading", async () => {
    const user = userEvent.setup();
    vi.mocked(api.register).mockImplementationOnce(() => new Promise(() => {}));

    render(<RegisterPage />);

    await user.type(screen.getByLabelText("Email"), "john@example.com");
    await user.type(screen.getByLabelText("Password"), "password123");

    const submitButton = screen.getByRole("button", {
      name: /create account/i,
    });
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

  it("has link to login page", () => {
    render(<RegisterPage />);
    const signInLink = screen.getByRole("link", { name: /sign in/i });
    expect(signInLink).toHaveAttribute("href", "/login");
  });

  it("displays terms of service text with links", () => {
    render(<RegisterPage />);
    expect(
      screen.getByText(/by signing up, you agree to our/i),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: /terms of service/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: /privacy policy/i }),
    ).toBeInTheDocument();
  });
});
