import argparse
import os
import shutil
import subprocess
import sys
from typing import Optional

from terminal_a11y.screen_reader import ScreenReaderFilter
from terminal_a11y.photophobia import PhotophobiaFilter
from terminal_a11y.budget import BudgetFilter
from terminal_a11y.braille import BrailleFilter
from terminal_a11y.audio import AudioProgress
from terminal_a11y.errors import install_excepthook
from terminal_a11y.detection import is_screen_reader_active

__all__ = ["main", "build_parser", "run_wrapped"]


class _CommandAction(argparse.Action):
    """Strip the optional '--' separator from the captured command list."""

    def __call__(self, parser, namespace, values, option_string=None):
        if values and values[0] == "--":
            values = values[1:]
        setattr(namespace, self.dest, values)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="terminal-a11y",
        description="Accessibility enhancement layer for command-line output.",
    )
    parser.add_argument(
        "--screen-reader",
        "--sr",
        action="store_true",
        help="Linearise output for screen readers.",
    )
    parser.add_argument(
        "--photophobia",
        "--soft",
        action="store_true",
        help="Apply an amber phosphor palette to reduce halation.",
    )
    parser.add_argument(
        "--sensory-budget",
        type=int,
        metavar="N",
        default=None,
        help="Suppress output after N lines to prevent sensory overload (default 2000).",
    )
    parser.add_argument(
        "--braille",
        action="store_true",
        help="Format output for refreshable braille displays (40 columns, ASCII fallback).",
    )
    parser.add_argument(
        "--audio-progress",
        action="store_true",
        help="Play audio tones at estimated progress milestones as output streams.",
    )
    parser.add_argument(
        "--auto",
        action="store_true",
        help="Auto-enable --screen-reader if a screen reader is detected.",
    )
    parser.add_argument(
        "--explain-errors",
        action="store_true",
        help="Prefix unhandled exceptions with a plain-language summary.",
    )
    parser.add_argument(
        "command",
        nargs=argparse.REMAINDER,
        action=_CommandAction,
        help="Command to run, preceded by '--' if it begins with '-'.",
    )
    return parser


def _wrap_stream(stream, **flags) -> object:
    """
    Apply filters to ``stream`` in a predictable order.

    Order matters: braille width formatting first, then screen-reader
    linearisation, then photophobia palette, then budget throttling. Audio
    progress is handled separately.
    """
    if flags.get("braille"):
        stream = BrailleFilter(stream)
    if flags.get("screen_reader"):
        stream = ScreenReaderFilter(stream)
    if flags.get("photophobia"):
        stream = PhotophobiaFilter(stream)
    if flags.get("sensory_budget") is not None:
        stream = BudgetFilter(stream, threshold=flags["sensory_budget"])
    return stream


def run_wrapped(
    command: list[str],
    screen_reader: bool = False,
    photophobia: bool = False,
    sensory_budget: Optional[int] = None,
    braille: bool = False,
    audio_progress: bool = False,
    explain_errors: bool = False,
) -> int:
    """
    Run ``command`` and stream its stdout/stderr through the enabled filters.

    Returns the subprocess exit code.
    """
    if not command:
        print("terminal-a11y: no command provided", file=sys.stderr)
        return 2

    if explain_errors:
        install_excepthook(stream=sys.stderr)

    out_stream = sys.stdout
    err_stream = sys.stderr

    flags = {
        "screen_reader": screen_reader,
        "photophobia": photophobia,
        "sensory_budget": sensory_budget,
        "braille": braille,
    }

    out_stream = _wrap_stream(out_stream, **flags)
    if screen_reader or braille or photophobia or sensory_budget is not None:
        err_stream = _wrap_stream(err_stream, **flags)

    audio = AudioProgress() if audio_progress else None

    try:
        proc = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
    except FileNotFoundError:
        print(f"terminal-a11y: command not found: {command[0]}", file=sys.stderr)
        return 127
    except Exception as exc:
        print(f"terminal-a11y: failed to start command: {exc}", file=sys.stderr)
        return 1

    audio_percent = 0
    try:
        while True:
            stdout_data = proc.stdout.readline() if proc.stdout else ""
            stderr_data = proc.stderr.readline() if proc.stderr else ""
            if stdout_data:
                out_stream.write(stdout_data)
                out_stream.flush()
                if audio is not None:
                    audio_percent = min(100, audio_percent + 1)
                    audio.report(audio_percent)
            if stderr_data:
                err_stream.write(stderr_data)
                err_stream.flush()
            if not stdout_data and not stderr_data and proc.poll() is not None:
                break
    finally:
        # Flush any remaining buffered output in filters.
        for stream in (out_stream, err_stream):
            try:
                stream.flush()
            except Exception:
                pass
        if audio is not None:
            audio.report(100)
            audio.close()
        proc.wait()

    if screen_reader and hasattr(out_stream, "inject_bell"):
        out_stream.inject_bell()

    return proc.returncode


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.auto and is_screen_reader_active():
        args.screen_reader = True

    if args.sensory_budget is None and not any([
        args.screen_reader,
        args.photophobia,
        args.braille,
        args.audio_progress,
        args.explain_errors,
    ]):
        print(
            "terminal-a11y: no accessibility mode enabled. "
            "Use --help to see available flags.",
            file=sys.stderr,
        )
        return 2

    # Default budget threshold when flag is passed without a value.
    if args.sensory_budget is not None and args.sensory_budget == 0:
        args.sensory_budget = 2000

    return run_wrapped(
        command=args.command,
        screen_reader=args.screen_reader,
        photophobia=args.photophobia,
        sensory_budget=args.sensory_budget,
        braille=args.braille,
        audio_progress=args.audio_progress,
        explain_errors=args.explain_errors,
    )


if __name__ == "__main__":
    sys.exit(main())
