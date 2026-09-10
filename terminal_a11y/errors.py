import re
import sys
import traceback
from types import TracebackType
from typing import Optional, Type

__all__ = ["ERROR_PATTERNS", "explain_exception", "install_excepthook", "ErrorExplainer"]

ERROR_PATTERNS: dict[str, str] = {
    "ConnectionRefusedError": "The program tried to connect to another computer or service, but that service refused the connection. It may be offline, not running, or blocking requests.",
    "ConnectionError": "A network connection failed. Check your internet connection, the remote address, or whether a firewall is blocking the request.",
    "PermissionError": "The program does not have permission to access a file, folder, or resource. Try running with appropriate permissions or choose a different location.",
    "FileNotFoundError": "The program could not find a file or folder it expected to exist. Check the path and spelling.",
    "IsADirectoryError": "The program tried to use a folder as if it were a file.",
    "NotADirectoryError": "The program expected a folder but found a file instead.",
    "TimeoutError": "An operation took too long and timed out. The remote service may be slow or unreachable.",
    "ValueError": "The program received data it could not understand or use in this context.",
    "TypeError": "The program was asked to do something with the wrong kind of data.",
    "KeyError": "The program looked for a named item that does not exist.",
    "IndexError": "The program tried to access a position in a list that does not exist.",
    "AttributeError": "The program tried to use a feature that the current data does not support.",
    "ModuleNotFoundError": "The program needs a Python module or package that is not installed.",
    "ImportError": "The program failed to import something it needs.",
    "RuntimeError": "The program encountered a general error while running.",
    "OSError": "The operating system reported an error, often related to files, networks, or devices.",
    "MemoryError": "The program ran out of available memory.",
    "RecursionError": "The program called itself too many times and exceeded Python's recursion limit.",
    "ZeroDivisionError": "The program tried to divide a number by zero.",
    "AssertionError": "An internal check failed. The program assumed something was true that was not.",
}

_EXCEPTION_RE: dict[Type[BaseException], str] = {}


def explain_exception(exc: BaseException) -> str:
    """
    Return a plain-language explanation for a standard exception.

    Falls back to a generic message for unknown exception types.
    """
    name = type(exc).__name__

    # Message-based fallback takes precedence so generic wrappers like
    # OSError("Connection refused...") are explained meaningfully.
    message = str(exc).lower()
    if "connection refused" in message:
        return ERROR_PATTERNS["ConnectionRefusedError"]
    if "timed out" in message or "timeout" in message:
        return ERROR_PATTERNS["TimeoutError"]
    if "permission denied" in message:
        return ERROR_PATTERNS["PermissionError"]
    if "no such file" in message or "cannot find" in message:
        return ERROR_PATTERNS["FileNotFoundError"]

    if name in ERROR_PATTERNS:
        return ERROR_PATTERNS[name]

    return f"The program encountered an unexpected error ({name})."


def _compose_explanation(
    exc_type: Optional[Type[BaseException]],
    exc_value: Optional[BaseException],
    exc_tb: Optional[TracebackType],
) -> str:
    """Build a user-facing explanation string from exception details."""
    if exc_type is None or exc_value is None:
        return ""

    explanation = explain_exception(exc_value)
    header = f"\n[Accessible summary] {explanation}\n"
    return header


def install_excepthook(
    stream: Optional[object] = None,
    include_trace: bool = True,
) -> None:
    """
    Install a sys.excepthook that prefixes unhandled exceptions with a plain-language summary.

    Args:
        stream: Output stream. Defaults to sys.stderr.
        include_trace: If True, the original traceback is printed after the summary.
    """
    target = stream or sys.stderr
    original_hook = sys.excepthook

    def accessible_excepthook(
        exc_type: Type[BaseException],
        exc_value: BaseException,
        exc_tb: Optional[TracebackType],
    ) -> None:
        summary = _compose_explanation(exc_type, exc_value, exc_tb)
        target.write(summary)
        target.flush()
        if include_trace:
            original_hook(exc_type, exc_value, exc_tb)
        else:
            target.write(f"{exc_type.__name__}: {exc_value}\n")
            target.flush()

    sys.excepthook = accessible_excepthook


class ErrorExplainer:
    """
    A context manager that temporarily installs the accessible exception hook.
    """

    def __init__(self, stream: Optional[object] = None, include_trace: bool = True):
        self.stream = stream or sys.stderr
        self.include_trace = include_trace
        self._original_hook: Optional[object] = None

    def __enter__(self) -> "ErrorExplainer":
        self._original_hook = sys.excepthook
        install_excepthook(self.stream, self.include_trace)
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        if self._original_hook is not None:
            sys.excepthook = self._original_hook
        self._original_hook = None
