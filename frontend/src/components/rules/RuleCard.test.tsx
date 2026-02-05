import { describe, it, expect, vi } from "vitest";
import { render, screen } from "../../test/utils";
import userEvent from "@testing-library/user-event";
import { RuleCard } from "./RuleCard";
import type { Rule } from "../../lib/rulesApi";

const mockRule: Rule = {
  id: 1,
  name: "Tech News Rule",
  include_keywords: "technology,ai,machine learning",
  exclude_keywords: "crypto,bitcoin",
  collection_id: 1,
  frequency_minutes: 60,
  last_run_at: null,
  is_active: true,
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
};

describe("RuleCard", () => {
  it("renders rule name", () => {
    render(<RuleCard rule={mockRule} />);

    expect(screen.getByText("Tech News Rule")).toBeInTheDocument();
  });

  it("shows Active badge when rule is active", () => {
    render(<RuleCard rule={mockRule} />);

    expect(screen.getByText("Active")).toBeInTheDocument();
  });

  it("shows Paused badge when rule is inactive", () => {
    const inactiveRule = { ...mockRule, is_active: false };
    render(<RuleCard rule={inactiveRule} />);

    expect(screen.getByText("Paused")).toBeInTheDocument();
  });

  it("renders include keywords as tags", () => {
    render(<RuleCard rule={mockRule} />);

    expect(screen.getByText("technology")).toBeInTheDocument();
    expect(screen.getByText("ai")).toBeInTheDocument();
    expect(screen.getByText("machine learning")).toBeInTheDocument();
  });

  it("renders exclude keywords as tags", () => {
    render(<RuleCard rule={mockRule} />);

    expect(screen.getByText("crypto")).toBeInTheDocument();
    expect(screen.getByText("bitcoin")).toBeInTheDocument();
  });

  it("shows frequency in hours for 60 minutes", () => {
    render(<RuleCard rule={mockRule} />);

    expect(screen.getByText("Every 1h")).toBeInTheDocument();
  });

  it("shows frequency in minutes for less than 60 minutes", () => {
    const rule = { ...mockRule, frequency_minutes: 30 };
    render(<RuleCard rule={rule} />);

    expect(screen.getByText("Every 30 min")).toBeInTheDocument();
  });

  it("shows frequency in days for 24+ hours", () => {
    const rule = { ...mockRule, frequency_minutes: 1440 };
    render(<RuleCard rule={rule} />);

    expect(screen.getByText("Every 1d")).toBeInTheDocument();
  });

  it("shows 'Never run' when last_run_at is null", () => {
    render(<RuleCard rule={mockRule} />);

    expect(screen.getByText("Never run")).toBeInTheDocument();
  });

  it("shows collection name when provided", () => {
    render(<RuleCard rule={mockRule} collectionName="Tech News" />);

    expect(screen.getByText("Tech News")).toBeInTheDocument();
  });

  it("calls onEdit when edit button is clicked", async () => {
    const user = userEvent.setup();
    const onEdit = vi.fn();
    render(<RuleCard rule={mockRule} onEdit={onEdit} />);

    await user.click(screen.getByRole("button", { name: /edit rule/i }));

    expect(onEdit).toHaveBeenCalled();
  });

  it("calls onDelete when delete button is clicked", async () => {
    const user = userEvent.setup();
    const onDelete = vi.fn();
    render(<RuleCard rule={mockRule} onDelete={onDelete} />);

    await user.click(screen.getByRole("button", { name: /delete rule/i }));

    expect(onDelete).toHaveBeenCalled();
  });

  it("calls onToggleActive when pause/play button is clicked", async () => {
    const user = userEvent.setup();
    const onToggleActive = vi.fn();
    render(<RuleCard rule={mockRule} onToggleActive={onToggleActive} />);

    await user.click(screen.getByRole("button", { name: /pause rule/i }));

    expect(onToggleActive).toHaveBeenCalled();
  });

  it("shows activate button when rule is inactive", () => {
    const inactiveRule = { ...mockRule, is_active: false };
    render(<RuleCard rule={inactiveRule} onToggleActive={() => {}} />);

    expect(
      screen.getByRole("button", { name: /activate rule/i }),
    ).toBeInTheDocument();
  });

  it("disables buttons when disabled prop is true", () => {
    render(
      <RuleCard
        rule={mockRule}
        onEdit={() => {}}
        onDelete={() => {}}
        onToggleActive={() => {}}
        disabled={true}
      />,
    );

    expect(screen.getByRole("button", { name: /edit rule/i })).toBeDisabled();
    expect(screen.getByRole("button", { name: /delete rule/i })).toBeDisabled();
    expect(screen.getByRole("button", { name: /pause rule/i })).toBeDisabled();
  });

  it("shows 'No keywords configured' when no keywords are set", () => {
    const ruleWithoutKeywords = {
      ...mockRule,
      include_keywords: null,
      exclude_keywords: null,
    };
    render(<RuleCard rule={ruleWithoutKeywords} />);

    expect(screen.getByText("No keywords configured")).toBeInTheDocument();
  });

  it("applies inactive class when rule is inactive", () => {
    const inactiveRule = { ...mockRule, is_active: false };
    const { container } = render(<RuleCard rule={inactiveRule} />);

    expect((container.firstChild as HTMLElement)?.className).toMatch(
      /inactive/,
    );
  });
});
