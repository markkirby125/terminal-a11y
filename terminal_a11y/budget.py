import sys
from typing import Optional, TextIO

__all__ = ["SensoryBudget", "BudgetFilter"]

DEFAULT_LINE_BUDGET = 2000


class SensoryBudget:
    """
    Tracks how many lines have been emitted in a session and decides when to throttle.
    """

    def __init__(self, threshold: int = DEFAULT_LINE_BUDGET):
        if threshold < 0:
            raise ValueError("Threshold must be non-negative")
        self.threshold = threshold
        self.lines_seen = 0
        self.lines_suppressed = 0
        self._summary_shown = False

    def count_lines(self, text: str) -> int:
        """Count the number of newline characters in a text block."""
        if not text:
            return 0
        return text.count("\n")

    def allocate(self, text: str) -> tuple[str, bool]:
        """
        Decide how much of ``text`` can be emitted.

        Returns a tuple of (emit_text, was_truncated). Once the budget is
        exceeded, text is accumulated as suppressed and an empty string is
        returned. A summary line is emitted the first time the budget is
        exceeded.
        """
        if self.threshold == 0:
            self.lines_suppressed += self.count_lines(text)
            if not self._summary_shown:
                self._summary_shown = True
                return self._summary_line(), True
            return "", True

        incoming = self.count_lines(text)

        if self.lines_seen + incoming <= self.threshold:
            self.lines_seen += incoming
            return text, False

        result: list[str] = []
        for char in text:
            if char == "\n":
                if self.lines_seen < self.threshold:
                    self.lines_seen += 1
                    result.append(char)
                else:
                    self.lines_suppressed += 1
                    if not self._summary_shown:
                        self._summary_shown = True
                        result.append(self._summary_line())
            elif self.lines_seen < self.threshold:
                result.append(char)

        if self.lines_seen >= self.threshold and not self._summary_shown:
            self._summary_shown = True
            result.append(self._summary_line())

        return "".join(result), True

    def _summary_line(self) -> str:
        return f"\n[Sensory budget] {self.lines_suppressed} lines suppressed to reduce overload.\n"

    def reset(self) -> None:
        """Reset the budget counters for a new session."""
        self.lines_seen = 0
        self.lines_suppressed = 0
        self._summary_shown = False


class BudgetFilter:
    """
    A stream filter that throttles output once a line budget is exceeded.
    """

    def __init__(
        self,
        stream: TextIO = sys.stdout,
        threshold: int = DEFAULT_LINE_BUDGET,
    ):
        self.stream = stream
        self.budget = SensoryBudget(threshold)
        self._closed = False

    def write(self, data: str) -> None:
        if self._closed:
            return
        emitted, _ = self.budget.allocate(data)
        if emitted:
            self.stream.write(emitted)

    def flush(self) -> None:
        self.stream.flush()

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        self.flush()

    def reset(self) -> None:
        """Reset the budget for a new run."""
        self.budget.reset()

    def __getattr__(self, attr):
        return getattr(self.stream, attr)
