"""Rule scheduling logic for periodic rule execution.

This module provides functions to determine which rules are due for execution
and to run them. It is designed to be called by an external scheduler
(e.g., Celery beat, cron) at regular intervals.

Timezone Handling
-----------------
All datetime comparisons use UTC. The caller should pass `now` as a
timezone-aware UTC datetime (e.g., `datetime.now(UTC)`).

For SQLite testing, datetime comparisons are done in Python after fetching
candidates, since SQLite doesn't handle timezone-aware datetime arithmetic
well. For PostgreSQL in production, the query could be optimized to filter
in the database.

Scheduling Semantics
--------------------
A rule is considered "due" if ALL of the following are true:
1. `is_active == True` - Rule must be enabled
2. `frequency_minutes > 0` - Zero frequency disables scheduling
3. Either:
   - `last_run_at is NULL` - Never run, due immediately
   - `now - last_run_at >= frequency_minutes` - Interval has elapsed

Failure Handling
----------------
If a single rule fails during `run_due_rules`, the error is logged and
counted, but execution continues to the next rule. This ensures one
broken rule doesn't block all other rules from running.

The `last_run_at` timestamp is only updated by `run_rule` on successful
execution. If a rule fails, its `last_run_at` remains unchanged, so it
will be picked up again on the next scheduler run.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.rule import Rule
from app.workers.rule_runner import run_rule

logger = logging.getLogger(__name__)


@dataclass
class RunDueRulesResult:
    """Result of running all due rules.

    Attributes:
        rules_due: Number of rules that were due for execution.
        rules_run: Number of rules that were successfully executed.
        failures: Number of rules that failed during execution.
    """

    rules_due: int
    rules_run: int
    failures: int


def get_due_rules(now: datetime, session: Session) -> list[Rule]:
    """Get all rules that are due for execution.

    A rule is due if:
    - is_active == True
    - frequency_minutes > 0 (zero disables scheduling)
    - last_run_at is NULL (never run), OR
    - now - last_run_at >= frequency_minutes

    Note on implementation:
    We fetch all active rules with frequency > 0 and filter in Python.
    This is simpler and works consistently across SQLite (tests) and
    PostgreSQL (production). For large rule sets, consider optimizing
    with database-side filtering.

    Args:
        now: The current UTC datetime. Should be timezone-aware.
        session: Database session for queries.

    Returns:
        List of Rule objects that are due for execution.

    Example:
        >>> now = datetime.now(UTC)
        >>> due_rules = get_due_rules(now, session)
        >>> for rule in due_rules:
        ...     run_rule(rule.id, session)
    """
    # Fetch candidate rules: active with frequency > 0
    query = select(Rule).where(Rule.is_active == True, Rule.frequency_minutes > 0)  # noqa: E712
    candidates = list(session.execute(query).scalars().all())

    due_rules: list[Rule] = []
    for rule in candidates:
        if _is_rule_due(rule, now):
            due_rules.append(rule)

    logger.debug(
        "Due rules check completed",
        extra={"candidates": len(candidates), "due": len(due_rules)},
    )

    return due_rules


def _is_rule_due(rule: Rule, now: datetime) -> bool:
    """Check if a single rule is due for execution.

    Args:
        rule: The rule to check.
        now: The current UTC datetime.

    Returns:
        True if the rule is due, False otherwise.
    """
    # Never run => due immediately
    if rule.last_run_at is None:
        return True

    # Calculate time since last run
    # Handle both timezone-aware and naive datetimes (SQLite returns naive)
    last_run = rule.last_run_at
    if last_run.tzinfo is None:
        # Assume UTC for naive datetimes from SQLite
        last_run = last_run.replace(tzinfo=UTC)

    now_utc = now if now.tzinfo else now.replace(tzinfo=UTC)

    elapsed = now_utc - last_run
    required = timedelta(minutes=rule.frequency_minutes)

    return elapsed >= required


def run_due_rules(now: datetime, session: Session) -> RunDueRulesResult:
    """Run all rules that are due for execution.

    This function:
    1. Fetches all due rules using get_due_rules
    2. Runs each rule using run_rule
    3. Continues to next rule if one fails (partial failure handling)
    4. Returns counters for monitoring

    The `last_run_at` is updated by `run_rule` on success, so failed rules
    will be picked up again on the next scheduler run.

    Args:
        now: The current UTC datetime. Should be timezone-aware.
        session: Database session for queries and persistence.

    Returns:
        RunDueRulesResult with execution statistics.

    Example:
        >>> now = datetime.now(UTC)
        >>> result = run_due_rules(now, session)
        >>> print(f"Ran {result.rules_run}/{result.rules_due}, {result.failures} failures")
    """
    due_rules = get_due_rules(now, session)

    rules_run = 0
    failures = 0

    logger.info(
        "Starting scheduled rule execution", extra={"due_count": len(due_rules)}
    )

    for rule in due_rules:
        try:
            logger.info(
                "Running scheduled rule",
                extra={"rule_id": rule.id, "rule_name": rule.name},
            )
            run_rule(rule.id, session)
            rules_run += 1
            logger.info("Scheduled rule completed", extra={"rule_id": rule.id})
        except Exception:
            failures += 1
            logger.exception(
                "Scheduled rule failed",
                extra={"rule_id": rule.id, "rule_name": rule.name},
            )
            # Continue to next rule - don't let one failure stop others

    logger.info(
        "Scheduled rule execution completed",
        extra={
            "rules_due": len(due_rules),
            "rules_run": rules_run,
            "failures": failures,
        },
    )

    return RunDueRulesResult(
        rules_due=len(due_rules),
        rules_run=rules_run,
        failures=failures,
    )
