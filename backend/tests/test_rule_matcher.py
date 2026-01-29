"""Unit tests for rule keyword matching logic.

Tests cover:
- Include keyword matching (any-of logic)
- Exclude keyword matching (exclude wins)
- Include + exclude combinations
- Empty/None keyword handling
- Case-insensitive matching
- Article fields missing or None
- Keyword with spaces
- Ignore empty strings in keyword lists
"""

from __future__ import annotations

from app.rules.matcher import matches_rule

# --- Fixtures for test data ---


class FakeRule:
    """Minimal rule-like object for testing."""

    def __init__(
        self,
        include_keywords: str | None = None,
        exclude_keywords: str | None = None,
    ):
        self.include_keywords = include_keywords
        self.exclude_keywords = exclude_keywords


class FakeArticle:
    """Minimal article-like object for testing."""

    def __init__(
        self,
        title: str = "",
        summary: str | None = None,
        content: str | None = None,
    ):
        self.title = title
        self.summary = summary
        self.content = content


# --- Include keyword tests ---


class TestIncludeKeywords:
    """Tests for include keyword matching."""

    def test_include_keyword_matches_in_title(self):
        """Include keyword found in title should match."""
        rule = FakeRule(include_keywords="python")
        article = FakeArticle(title="Learn Python Programming")

        assert matches_rule(rule, article) is True

    def test_include_keyword_matches_in_summary(self):
        """Include keyword found in summary should match."""
        rule = FakeRule(include_keywords="machine learning")
        article = FakeArticle(
            title="Tech News",
            summary="Deep dive into machine learning algorithms",
        )

        assert matches_rule(rule, article) is True

    def test_include_keyword_matches_in_content(self):
        """Include keyword found in content should match."""
        rule = FakeRule(include_keywords="fastapi")
        article = FakeArticle(
            title="Web Development",
            summary="Building APIs",
            content="We'll use FastAPI for our backend.",
        )

        assert matches_rule(rule, article) is True

    def test_include_keyword_not_found_does_not_match(self):
        """Article without include keyword should not match."""
        rule = FakeRule(include_keywords="rust")
        article = FakeArticle(title="Python is great")

        assert matches_rule(rule, article) is False

    def test_multiple_include_keywords_any_match(self):
        """Any one of multiple include keywords matching is sufficient."""
        rule = FakeRule(include_keywords="python,rust,golang")
        article = FakeArticle(title="Why Rust is memory safe")

        assert matches_rule(rule, article) is True

    def test_multiple_include_keywords_none_match(self):
        """None of the include keywords present should not match."""
        rule = FakeRule(include_keywords="python,rust,golang")
        article = FakeArticle(title="JavaScript frameworks in 2026")

        assert matches_rule(rule, article) is False

    def test_include_keyword_case_insensitive(self):
        """Matching should be case-insensitive."""
        rule = FakeRule(include_keywords="PYTHON")
        article = FakeArticle(title="python programming")

        assert matches_rule(rule, article) is True

    def test_include_keyword_mixed_case_in_article(self):
        """Mixed case in article should still match."""
        rule = FakeRule(include_keywords="python")
        article = FakeArticle(title="PyThOn Is Awesome")

        assert matches_rule(rule, article) is True


# --- Exclude keyword tests ---


class TestExcludeKeywords:
    """Tests for exclude keyword matching."""

    def test_exclude_keyword_blocks_match(self):
        """Exclude keyword found should block match."""
        rule = FakeRule(exclude_keywords="crypto")
        article = FakeArticle(title="Crypto market crashes again")

        assert matches_rule(rule, article) is False

    def test_exclude_keyword_not_found_allows_match(self):
        """No exclude keyword found should allow match."""
        rule = FakeRule(exclude_keywords="crypto")
        article = FakeArticle(title="Python programming tips")

        assert matches_rule(rule, article) is True

    def test_exclude_keyword_in_summary_blocks(self):
        """Exclude keyword in summary should block."""
        rule = FakeRule(exclude_keywords="bitcoin")
        article = FakeArticle(
            title="Financial News",
            summary="Bitcoin reaches new highs",
        )

        assert matches_rule(rule, article) is False

    def test_exclude_keyword_in_content_blocks(self):
        """Exclude keyword in content should block."""
        rule = FakeRule(exclude_keywords="advertisement")
        article = FakeArticle(
            title="Product Review",
            summary="Honest review",
            content="This is an advertisement for the product.",
        )

        assert matches_rule(rule, article) is False

    def test_multiple_exclude_keywords_any_blocks(self):
        """Any one of multiple exclude keywords should block."""
        rule = FakeRule(exclude_keywords="crypto,nft,blockchain")
        article = FakeArticle(title="Understanding NFT marketplaces")

        assert matches_rule(rule, article) is False

    def test_exclude_keyword_case_insensitive(self):
        """Exclude matching should be case-insensitive."""
        rule = FakeRule(exclude_keywords="SPAM")
        article = FakeArticle(title="This is spam content")

        assert matches_rule(rule, article) is False


# --- Include + Exclude combination tests ---


class TestIncludeExcludeCombination:
    """Tests for include + exclude keyword combinations."""

    def test_include_and_exclude_both_match_exclude_wins(self):
        """When both include and exclude match, exclude wins."""
        rule = FakeRule(
            include_keywords="python",
            exclude_keywords="beginner",
        )
        article = FakeArticle(title="Python for Beginners")

        assert matches_rule(rule, article) is False

    def test_include_matches_exclude_does_not(self):
        """Include matches, exclude doesn't -> match."""
        rule = FakeRule(
            include_keywords="python",
            exclude_keywords="java",
        )
        article = FakeArticle(title="Advanced Python Patterns")

        assert matches_rule(rule, article) is True

    def test_include_does_not_match_exclude_does_not(self):
        """Include doesn't match, exclude doesn't either -> no match."""
        rule = FakeRule(
            include_keywords="rust",
            exclude_keywords="java",
        )
        article = FakeArticle(title="Python is great")

        assert matches_rule(rule, article) is False

    def test_include_does_not_match_exclude_matches(self):
        """Include doesn't match, exclude matches -> no match."""
        rule = FakeRule(
            include_keywords="rust",
            exclude_keywords="python",
        )
        article = FakeArticle(title="Python tutorial")

        assert matches_rule(rule, article) is False


# --- Empty/None keyword handling tests ---


class TestEmptyKeywordHandling:
    """Tests for empty and None keyword handling."""

    def test_no_include_no_exclude_matches_all(self):
        """Rule with no keywords matches all articles."""
        rule = FakeRule(include_keywords=None, exclude_keywords=None)
        article = FakeArticle(title="Any article")

        assert matches_rule(rule, article) is True

    def test_empty_include_string_matches_all(self):
        """Empty include_keywords string should match all."""
        rule = FakeRule(include_keywords="", exclude_keywords=None)
        article = FakeArticle(title="Any article")

        assert matches_rule(rule, article) is True

    def test_whitespace_only_include_matches_all(self):
        """Whitespace-only include_keywords should match all."""
        rule = FakeRule(include_keywords="   ", exclude_keywords=None)
        article = FakeArticle(title="Any article")

        assert matches_rule(rule, article) is True

    def test_empty_exclude_string_does_not_block(self):
        """Empty exclude_keywords string should not block."""
        rule = FakeRule(include_keywords="python", exclude_keywords="")
        article = FakeArticle(title="Python programming")

        assert matches_rule(rule, article) is True

    def test_ignore_empty_keywords_in_list(self):
        """Empty strings in keyword list should be ignored."""
        rule = FakeRule(include_keywords="python,,rust,  ,golang")
        article = FakeArticle(title="Learning Rust")

        assert matches_rule(rule, article) is True

    def test_only_empty_keywords_in_include_matches_all(self):
        """List with only empty keywords should match all."""
        rule = FakeRule(include_keywords=",  , ,")
        article = FakeArticle(title="Any article")

        assert matches_rule(rule, article) is True

    def test_exclude_only_rule_matches_unless_excluded(self):
        """Rule with only exclude keywords matches all except excluded."""
        rule = FakeRule(include_keywords=None, exclude_keywords="spam")
        article = FakeArticle(title="Valid content")

        assert matches_rule(rule, article) is True

    def test_exclude_only_rule_blocks_excluded(self):
        """Rule with only exclude keywords blocks matching articles."""
        rule = FakeRule(include_keywords=None, exclude_keywords="spam")
        article = FakeArticle(title="This is spam")

        assert matches_rule(rule, article) is False


# --- Article field edge cases ---


class TestArticleFieldEdgeCases:
    """Tests for article field edge cases."""

    def test_article_with_none_summary_and_content(self):
        """Article with only title should still work."""
        rule = FakeRule(include_keywords="python")
        article = FakeArticle(title="Python tips", summary=None, content=None)

        assert matches_rule(rule, article) is True

    def test_article_with_empty_title(self):
        """Article with empty title checks other fields."""
        rule = FakeRule(include_keywords="python")
        article = FakeArticle(title="", summary="Learn Python", content=None)

        assert matches_rule(rule, article) is True

    def test_article_with_all_empty_fields_no_include(self):
        """Article with all empty fields matches if no include keywords."""
        rule = FakeRule(include_keywords=None, exclude_keywords=None)
        article = FakeArticle(title="", summary=None, content=None)

        assert matches_rule(rule, article) is True

    def test_article_with_all_empty_fields_with_include(self):
        """Article with all empty fields does not match include keywords."""
        rule = FakeRule(include_keywords="python")
        article = FakeArticle(title="", summary=None, content=None)

        assert matches_rule(rule, article) is False


# --- Keyword with spaces tests ---


class TestKeywordsWithSpaces:
    """Tests for multi-word keywords."""

    def test_keyword_with_spaces_matches(self):
        """Multi-word keyword should match as substring."""
        rule = FakeRule(include_keywords="machine learning")
        article = FakeArticle(title="Introduction to machine learning")

        assert matches_rule(rule, article) is True

    def test_keyword_with_spaces_partial_no_match(self):
        """Partial multi-word keyword should not match."""
        rule = FakeRule(include_keywords="machine learning")
        article = FakeArticle(title="machine and learning are separate")

        # Substring match: "machine learning" as whole phrase not found
        assert matches_rule(rule, article) is False

    def test_keyword_with_leading_trailing_spaces_trimmed(self):
        """Keywords with leading/trailing spaces should be trimmed."""
        rule = FakeRule(include_keywords="  python  ,  rust  ")
        article = FakeArticle(title="Python programming")

        assert matches_rule(rule, article) is True


# --- Substring matching verification ---


class TestSubstringMatching:
    """Tests to verify substring matching behavior."""

    def test_substring_match_within_word(self):
        """Keyword as substring within a larger word should match.

        Note: This is a limitation of substring matching - 'py' matches 'python'.
        If token-based matching is needed later, this test documents current behavior.
        """
        rule = FakeRule(include_keywords="py")
        article = FakeArticle(title="python programming")

        # Substring match: 'py' is found within 'python'
        assert matches_rule(rule, article) is True

    def test_exclude_substring_within_word_blocks(self):
        """Exclude keyword as substring blocks match."""
        rule = FakeRule(exclude_keywords="script")
        article = FakeArticle(title="JavaScript frameworks")

        # 'script' found within 'JavaScript'
        assert matches_rule(rule, article) is False
