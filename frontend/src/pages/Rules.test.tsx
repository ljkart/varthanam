import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "../test/utils";
import userEvent from "@testing-library/user-event";
import { RulesPage } from "./Rules";
import { useRules } from "../hooks/useRules";
import { useCollections } from "../hooks/useCollections";
import type { Rule } from "../lib/rulesApi";
import type { Collection } from "../lib/collectionsApi";

// Mock the hooks
vi.mock("../hooks/useRules", () => ({
  useRules: vi.fn(),
}));

vi.mock("../hooks/useCollections", () => ({
  useCollections: vi.fn(),
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

const mockRule: Rule = {
  id: 1,
  name: "Tech News",
  include_keywords: "technology,ai",
  exclude_keywords: "crypto",
  collection_id: 1,
  frequency_minutes: 60,
  last_run_at: null,
  is_active: true,
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
};

const mockCollection: Collection = {
  id: 1,
  name: "Tech",
  description: "Technology news",
  user_id: 1,
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
};

const mockUseRules = {
  rules: [] as Rule[],
  isLoading: false,
  error: null,
  createRule: vi.fn(),
  updateRule: vi.fn(),
  deleteRule: vi.fn(),
  toggleRuleActive: vi.fn(),
  clearError: vi.fn(),
  fetchRules: vi.fn(),
};

const mockUseCollections = {
  collections: [mockCollection] as Collection[],
  isLoading: false,
  error: null,
  refetch: vi.fn(),
  createCollection: vi.fn(),
  updateCollection: vi.fn(),
  deleteCollection: vi.fn(),
};

describe("RulesPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useRules).mockReturnValue({ ...mockUseRules });
    vi.mocked(useCollections).mockReturnValue({ ...mockUseCollections });
  });

  it("renders page title", () => {
    render(<RulesPage />);

    expect(screen.getByText("Rules")).toBeInTheDocument();
  });

  it("renders intro text", () => {
    render(<RulesPage />);

    expect(
      screen.getByText(/Rules automatically filter and organize articles/),
    ).toBeInTheDocument();
  });

  it("shows loading state", () => {
    vi.mocked(useRules).mockReturnValue({
      ...mockUseRules,
      isLoading: true,
    });

    render(<RulesPage />);

    expect(screen.getByText("Loading rules...")).toBeInTheDocument();
  });

  it("shows empty state when no rules", () => {
    render(<RulesPage />);

    expect(screen.getByText("No rules yet")).toBeInTheDocument();
  });

  it("renders rules list", () => {
    vi.mocked(useRules).mockReturnValue({
      ...mockUseRules,
      rules: [mockRule],
    });

    render(<RulesPage />);

    expect(screen.getByText("Tech News")).toBeInTheDocument();
  });

  it("opens create modal when Create Rule button is clicked", async () => {
    const user = userEvent.setup();
    vi.mocked(useRules).mockReturnValue({
      ...mockUseRules,
      rules: [mockRule], // Show a rule so empty state button isn't shown
    });
    render(<RulesPage />);

    // Click the header Create Rule button
    const createButtons = screen.getAllByRole("button", {
      name: /create rule/i,
    });
    await user.click(createButtons[0]);

    expect(screen.getByRole("dialog")).toBeInTheDocument();
  });

  it("opens edit modal when edit button is clicked", async () => {
    const user = userEvent.setup();
    vi.mocked(useRules).mockReturnValue({
      ...mockUseRules,
      rules: [mockRule],
    });

    render(<RulesPage />);

    await user.click(screen.getByRole("button", { name: /edit rule/i }));

    expect(screen.getByRole("dialog")).toBeInTheDocument();
    expect(screen.getByText("Edit Rule")).toBeInTheDocument();
  });

  it("opens delete confirmation when delete button is clicked", async () => {
    const user = userEvent.setup();
    vi.mocked(useRules).mockReturnValue({
      ...mockUseRules,
      rules: [mockRule],
    });

    render(<RulesPage />);

    await user.click(screen.getByRole("button", { name: /delete rule/i }));

    expect(screen.getByText("Delete Rule")).toBeInTheDocument();
    expect(
      screen.getByText(/Are you sure you want to delete/),
    ).toBeInTheDocument();
  });

  it("calls createRule when form is submitted for new rule", async () => {
    const user = userEvent.setup();
    const createRule = vi.fn().mockResolvedValue(mockRule);
    vi.mocked(useRules).mockReturnValue({
      ...mockUseRules,
      rules: [mockRule], // Show a rule so empty state button isn't shown
      createRule,
    });

    render(<RulesPage />);

    // Click the header Create Rule button
    const createButtons = screen.getAllByRole("button", {
      name: /create rule/i,
    });
    await user.click(createButtons[0]);
    await user.type(screen.getByLabelText(/rule name/i), "New Rule");

    // The submit button in the modal
    const submitButtons = screen.getAllByRole("button", {
      name: /create rule/i,
    });
    const modalSubmitButton = submitButtons[submitButtons.length - 1]; // Last one is in the modal
    await user.click(modalSubmitButton);

    await waitFor(() => {
      expect(createRule).toHaveBeenCalled();
    });
  });

  it("calls updateRule when form is submitted for existing rule", async () => {
    const user = userEvent.setup();
    const updateRule = vi.fn().mockResolvedValue(mockRule);
    vi.mocked(useRules).mockReturnValue({
      ...mockUseRules,
      rules: [mockRule],
      updateRule,
    });

    render(<RulesPage />);

    await user.click(screen.getByRole("button", { name: /edit rule/i }));
    await user.clear(screen.getByLabelText(/rule name/i));
    await user.type(screen.getByLabelText(/rule name/i), "Updated Rule");
    await user.click(screen.getByRole("button", { name: /save changes/i }));

    await waitFor(() => {
      expect(updateRule).toHaveBeenCalledWith(
        1,
        expect.objectContaining({
          name: "Updated Rule",
        }),
      );
    });
  });

  it("calls deleteRule when delete is confirmed", async () => {
    const user = userEvent.setup();
    const deleteRule = vi.fn().mockResolvedValue(true);
    vi.mocked(useRules).mockReturnValue({
      ...mockUseRules,
      rules: [mockRule],
      deleteRule,
    });

    render(<RulesPage />);

    await user.click(screen.getByRole("button", { name: /delete rule/i }));
    await user.click(screen.getByRole("button", { name: /^delete$/i }));

    expect(deleteRule).toHaveBeenCalledWith(1);
  });

  it("calls toggleRuleActive when toggle button is clicked", async () => {
    const user = userEvent.setup();
    const toggleRuleActive = vi.fn().mockResolvedValue(true);
    vi.mocked(useRules).mockReturnValue({
      ...mockUseRules,
      rules: [mockRule],
      toggleRuleActive,
    });

    render(<RulesPage />);

    await user.click(screen.getByRole("button", { name: /pause rule/i }));

    expect(toggleRuleActive).toHaveBeenCalledWith(1);
  });

  it("displays error message when error occurs", () => {
    vi.mocked(useRules).mockReturnValue({
      ...mockUseRules,
      error: "Something went wrong",
    });

    render(<RulesPage />);

    expect(screen.getByText("Something went wrong")).toBeInTheDocument();
  });

  it("calls clearError when dismiss button is clicked", async () => {
    const user = userEvent.setup();
    const clearError = vi.fn();
    vi.mocked(useRules).mockReturnValue({
      ...mockUseRules,
      error: "Error",
      clearError,
    });

    render(<RulesPage />);

    await user.click(screen.getByRole("button", { name: /dismiss error/i }));

    expect(clearError).toHaveBeenCalled();
  });

  it("navigates back when back button is clicked", async () => {
    const user = userEvent.setup();
    render(<RulesPage />);

    await user.click(screen.getByRole("button", { name: /back/i }));

    expect(mockNavigate).toHaveBeenCalledWith("/app");
  });

  it("closes modal when Cancel is clicked", async () => {
    const user = userEvent.setup();
    vi.mocked(useRules).mockReturnValue({
      ...mockUseRules,
      rules: [mockRule], // Show a rule so empty state button isn't shown
    });
    render(<RulesPage />);

    // Click the header Create Rule button
    const createButtons = screen.getAllByRole("button", {
      name: /create rule/i,
    });
    await user.click(createButtons[0]);
    expect(screen.getByRole("dialog")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /cancel/i }));

    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("closes delete modal when Cancel is clicked", async () => {
    const user = userEvent.setup();
    vi.mocked(useRules).mockReturnValue({
      ...mockUseRules,
      rules: [mockRule],
    });

    render(<RulesPage />);

    await user.click(screen.getByRole("button", { name: /delete rule/i }));
    expect(screen.getByText("Delete Rule")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /cancel/i }));

    expect(screen.queryByText("Delete Rule")).not.toBeInTheDocument();
  });

  it("shows collection name on rule card", () => {
    vi.mocked(useRules).mockReturnValue({
      ...mockUseRules,
      rules: [mockRule],
    });

    render(<RulesPage />);

    expect(screen.getByText("Tech")).toBeInTheDocument();
  });
});
