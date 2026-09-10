import pytest
from terminal_a11y.errors import (
    ERROR_PATTERNS,
    explain_exception,
    ErrorExplainer,
)


class DummyConnectionRefused(ConnectionRefusedError):
    pass


@pytest.mark.parametrize(
    "exc_class,expected_fragment",
    [
        (ConnectionRefusedError, "refused the connection"),
        (PermissionError, "does not have permission"),
        (FileNotFoundError, "could not find"),
        (TimeoutError, "timed out"),
        (ValueError, "received data"),
        (TypeError, "wrong kind of data"),
        (KeyError, "named item"),
        (IndexError, "position in a list"),
        (AttributeError, "feature"),
        (ModuleNotFoundError, "not installed"),
        (ZeroDivisionError, "divide"),
        (RecursionError, "recursion limit"),
    ],
)
def test_known_exception_explanations(exc_class, expected_fragment):
    exc = exc_class("detail")
    explanation = explain_exception(exc)
    assert expected_fragment in explanation


def test_message_fallback_connection_refused():
    exc = OSError("Connection refused by peer")
    assert "refused the connection" in explain_exception(exc)


def test_message_fallback_permission_denied():
    exc = RuntimeError("Permission denied while accessing resource")
    assert "does not have permission" in explain_exception(exc)


def test_unknown_exception_fallback():
    class CustomError(Exception):
        pass

    exc = CustomError("something weird")
    explanation = explain_exception(exc)
    assert "CustomError" in explanation
    assert "unexpected error" in explanation


def test_error_explainer_restores_hook(monkeypatch):
    import sys
    original = sys.excepthook
    with ErrorExplainer(stream=sys.stderr):
        assert sys.excepthook is not original
    assert sys.excepthook is original
