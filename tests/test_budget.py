import pytest
from terminal_a11y.budget import SensoryBudget, BudgetFilter


def test_budget_allows_text_under_threshold():
    budget = SensoryBudget(threshold=5)
    emitted, truncated = budget.allocate("line1\nline2\n")
    assert emitted == "line1\nline2\n"
    assert truncated is False
    assert budget.lines_seen == 2


def test_budget_truncates_at_threshold():
    budget = SensoryBudget(threshold=2)
    emitted, truncated = budget.allocate("line1\nline2\nline3\n")
    assert "line1" in emitted
    assert "[Sensory budget]" in emitted
    assert budget.lines_suppressed == 1
    assert truncated is True


def test_budget_suppresses_after_threshold():
    budget = SensoryBudget(threshold=2)
    budget.allocate("line1\nline2\nline3\n")
    emitted, truncated = budget.allocate("line4\nline5\n")
    assert emitted == ""
    assert truncated is True
    assert budget.lines_suppressed == 3


def test_budget_zero_threshold_suppresses_all():
    budget = SensoryBudget(threshold=0)
    emitted, truncated = budget.allocate("anything\n")
    assert "[Sensory budget]" in emitted
    assert budget.lines_suppressed == 1


def test_budget_reset():
    budget = SensoryBudget(threshold=1)
    budget.allocate("line1\nline2\n")
    budget.reset()
    assert budget.lines_seen == 0
    assert budget.lines_suppressed == 0


def test_budget_filter_stream():
    from io import StringIO
    stream = StringIO()
    filt = BudgetFilter(stream, threshold=2)
    filt.write("a\nb\nc\nd\n")
    filt.flush()
    output = stream.getvalue()
    assert output.startswith("a\nb\n")
    assert "[Sensory budget]" in output


def test_budget_filter_respects_threshold_argument():
    from io import StringIO
    stream = StringIO()
    filt = BudgetFilter(stream, threshold=1)
    filt.write("a\nb\n")
    filt.flush()
    assert "a" in stream.getvalue()
    assert "[Sensory budget]" in stream.getvalue()
