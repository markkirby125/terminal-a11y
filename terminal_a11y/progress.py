import sys
from typing import Iterable, TypeVar, Optional, TextIO, Iterator

T = TypeVar('T')

class MilestoneProgress:
    """
    A milestone-based progress reporter replacing high-frequency progress bars
    with accessible text milestones (e.g., 25%, 50%, 75%, 100%).
    """
    def __init__(
        self,
        iterable: Iterable[T],
        total: Optional[int] = None,
        prefix: str = "Progress:",
        file: Optional[TextIO] = None,
        milestones: Optional[list[int]] = None
    ):
        self.iterable = iterable
        try:
            self.total = total if total is not None else len(iterable)  # type: ignore
        except TypeError:
            self.total = None
            
        self.prefix = prefix
        self.file = file or sys.stdout
        self.milestones = sorted(milestones or [25, 50, 75, 100])
        self.current = 0
        self._next_milestone_idx = 0

    def __iter__(self) -> Iterator[T]:
        if self.total is None or self.total == 0:
            yield from self.iterable
            return

        for item in self.iterable:
            yield item
            self.current += 1
            
            percent = (self.current * 100) // self.total
            
            while (
                self._next_milestone_idx < len(self.milestones) and 
                percent >= self.milestones[self._next_milestone_idx]
            ):
                milestone = self.milestones[self._next_milestone_idx]
                self.file.write(f"{self.prefix} {milestone}%\n")
                self.file.flush()
                self._next_milestone_idx += 1

def track_progress(
    iterable: Iterable[T],
    total: Optional[int] = None,
    prefix: str = "Progress:",
    file: Optional[TextIO] = None
) -> Iterator[T]:
    """
    Wrapper for an iterable to report milestone-based progress.
    """
    return iter(MilestoneProgress(iterable, total=total, prefix=prefix, file=file))
