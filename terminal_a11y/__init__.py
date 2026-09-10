import sys
from typing import Optional

from terminal_a11y.ansi import strip_ansi
from terminal_a11y.color import get_color_level, ColorLevel
from terminal_a11y.detection import is_screen_reader_active
from terminal_a11y.screen_reader import ScreenReaderFilter
from terminal_a11y.photophobia import PhotophobiaFilter
from terminal_a11y.budget import BudgetFilter
from terminal_a11y.braille import BrailleFilter
from terminal_a11y.audio import AudioProgress
from terminal_a11y.errors import ErrorExplainer, install_excepthook
from terminal_a11y.progress import track_progress

__version__ = "0.3.0"

__all__ = [
    "TerminalAccessibilityEngine",
    "strip_ansi",
    "get_color_level",
    "ColorLevel",
    "is_screen_reader_active",
    "ScreenReaderFilter",
    "PhotophobiaFilter",
    "BudgetFilter",
    "BrailleFilter",
    "AudioProgress",
    "ErrorExplainer",
    "install_excepthook",
    "track_progress",
    "__version__",
]


class TerminalAccessibilityEngine:
    """
    High-level convenience wrapper that installs one or more accessibility
    filters on ``sys.stdout`` (and optionally ``sys.stderr``).
    """

    def __init__(
        self,
        screen_reader: bool = False,
        photophobia: bool = False,
        sensory_budget: Optional[int] = None,
        braille: bool = False,
        audio_progress: bool = False,
        explain_errors: bool = False,
        auto_detect: bool = False,
        stderr: bool = True,
    ):
        self.screen_reader = screen_reader or (auto_detect and is_screen_reader_active())
        self.photophobia = photophobia
        self.sensory_budget = sensory_budget
        self.braille = braille
        self.audio_progress = audio_progress
        self.explain_errors = explain_errors
        self._stderr = stderr
        self._original_stdout = sys.stdout
        self._original_stderr = sys.stderr
        self._audio: Optional[AudioProgress] = None

    def __enter__(self) -> "TerminalAccessibilityEngine":
        if self.explain_errors:
            install_excepthook(stream=self._original_stderr)

        sys.stdout = self._wrap_stream(self._original_stdout)
        if self._stderr:
            sys.stderr = self._wrap_stream(self._original_stderr)

        if self.audio_progress:
            self._audio = AudioProgress()

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Ensure filters flush and reset.
        for stream in (sys.stdout, sys.stderr):
            try:
                stream.flush()
            except Exception:
                pass

        sys.stdout = self._original_stdout
        sys.stderr = self._original_stderr

        if self._audio is not None:
            self._audio.close()

        if self.screen_reader:
            self._original_stdout.write("\a")
            self._original_stdout.flush()

    def _wrap_stream(self, stream):
        if self.braille:
            stream = BrailleFilter(stream)
        if self.screen_reader:
            stream = ScreenReaderFilter(stream)
        if self.photophobia:
            stream = PhotophobiaFilter(stream)
        if self.sensory_budget is not None:
            threshold = self.sensory_budget if self.sensory_budget > 0 else 2000
            stream = BudgetFilter(stream, threshold=threshold)
        return stream

    def report_progress(self, percent: int) -> None:
        """If audio progress is enabled, play the next reached milestone tone."""
        if self._audio is not None:
            self._audio.report(percent)
