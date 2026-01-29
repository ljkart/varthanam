"""Rule keyword matching logic for article filtering.

This module provides pure, deterministic functions for matching articles
against rule keyword criteria. It is intentionally decoupled from FastAPI
and database concerns to remain testable and reusable.

Matching Semantics
------------------
- **Text sources**: title, summary, and content fields are searched.
- **Case-insensitive**: All matching is case-insensitive.
- **Substring matching**: Keywords are matched as substrings within the text.
  This means "py" will match "python". For token-based matching (word boundaries),
  a more complex implementation with regex would be needed.

Keyword Logic
-------------
- **Include keywords** (comma-separated):
  - If None or empty after parsing: matches all articles (unless excluded).
  - If present: at least ONE include keyword must match (any-of logic).

- **Exclude keywords** (comma-separated):
  - If ANY exclude keyword matches: rule does NOT match (exclude wins).
  - Exclude takes precedence over include.

- **Empty handling**: Empty strings and whitespace-only keywords are ignored.

Limitations
-----------
- Substring matching may produce false positives (e.g., "script" matches "JavaScript").
- For exact word matching, consider extending with regex word boundaries.
- No stemming or fuzzy matching is performed.
"""

from __future__ import annotations

from typing import Protocol


class RuleLike(Protocol):
    """Protocol for rule objects with keyword fields.

    This protocol allows the matcher to work with any object that has
    include_keywords and exclude_keywords attributes, including ORM models
    and test fakes.
    """

    include_keywords: str | None
    exclude_keywords: str | None


class ArticleLike(Protocol):
    """Protocol for article objects with text fields.

    This protocol allows the matcher to work with any object that has
    title, summary, and content attributes.
    """

    title: str
    summary: str | None
    content: str | None


def _parse_keywords(keywords_str: str | None) -> list[str]:
    """Parse comma-separated keywords string into a list of trimmed, non-empty keywords.

    Args:
        keywords_str: Comma-separated keywords string, or None.

    Returns:
        List of trimmed, non-empty keyword strings. Empty strings and
        whitespace-only entries are filtered out.

    Examples:
        >>> _parse_keywords("python, rust, golang")
        ['python', 'rust', 'golang']
        >>> _parse_keywords("  python  ,,  rust  ")
        ['python', 'rust']
        >>> _parse_keywords(None)
        []
        >>> _parse_keywords("")
        []
    """
    if not keywords_str:
        return []

    keywords = []
    for kw in keywords_str.split(","):
        stripped = kw.strip()
        if stripped:  # Ignore empty/whitespace-only
            keywords.append(stripped)
    return keywords


def _build_searchable_text(article: ArticleLike) -> str:
    """Combine article text fields into a single searchable string.

    Concatenates title, summary, and content (if present) into a single
    lowercase string for efficient keyword searching.

    Args:
        article: Article-like object with title, summary, and content fields.

    Returns:
        Lowercase string containing all available text fields joined by spaces.
    """
    parts = []

    # Title is typically required but handle empty string safely
    if article.title:
        parts.append(article.title)

    if article.summary:
        parts.append(article.summary)

    if article.content:
        parts.append(article.content)

    # Join with space and lowercase for case-insensitive matching
    return " ".join(parts).lower()


def _any_keyword_matches(keywords: list[str], text: str) -> bool:
    """Check if any keyword is found as a substring in the text.

    Args:
        keywords: List of keywords to search for (should be non-empty strings).
        text: Lowercase text to search within.

    Returns:
        True if any keyword is found in the text, False otherwise.
    """
    for keyword in keywords:
        # Case-insensitive: keyword is lowercased, text is already lowercase
        if keyword.lower() in text:
            return True
    return False


def matches_rule(rule: RuleLike, article: ArticleLike) -> bool:
    """Determine if an article matches a rule's keyword criteria.

    Matching Logic:
    1. Parse include and exclude keywords from comma-separated strings.
    2. If any exclude keyword is found in the article, return False (exclude wins).
    3. If no include keywords are specified, return True (match-all).
    4. If include keywords exist, return True only if at least one matches.

    Args:
        rule: Rule-like object with include_keywords and exclude_keywords.
        article: Article-like object with title, summary, and content fields.

    Returns:
        True if the article matches the rule's criteria, False otherwise.

    Examples:
        >>> # Include matches
        >>> matches_rule(rule_with_include="python", article_with_title="Python tutorial")
        True

        >>> # Exclude blocks
        >>> matches_rule(rule_with_exclude="spam", article_with_title="This is spam")
        False

        >>> # Exclude wins over include
        >>> matches_rule(
        ...     rule_with_include="python", rule_with_exclude="beginner",
        ...     article_with_title="Python for beginners"
        ... )
        False
    """
    include_keywords = _parse_keywords(rule.include_keywords)
    exclude_keywords = _parse_keywords(rule.exclude_keywords)

    # Build searchable text from article fields
    searchable_text = _build_searchable_text(article)

    # Step 1: Check excludes first (exclude wins)
    if exclude_keywords and _any_keyword_matches(exclude_keywords, searchable_text):
        return False

    # Step 2: If no include keywords, match all (that weren't excluded)
    if not include_keywords:
        return True

    # Step 3: Check if any include keyword matches
    return _any_keyword_matches(include_keywords, searchable_text)
