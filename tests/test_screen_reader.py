import pytest
from io import StringIO
from terminal_a11y.screen_reader import ScreenReaderFilter, linearize, format_header

def test_linearize_spinner():
    text = "Loading...\rDone!"
    assert linearize(text) == "Loading...\nDone!"

def test_linearize_crlf():
    text = "Line 1\r\nLine 2\r\n"
    assert linearize(text) == "Line 1\nLine 2\n"

def test_token_conversion():
    text = "Status: ✓ Success, ✗ Error, ⚠ Warning, ℹ Info"
    assert linearize(text) == "Status: [PASS] Success, [FAIL] Error, [WARN] Warning, [INFO] Info"

def test_bell_injection():
    out = StringIO()
    sr_filter = ScreenReaderFilter(out)
    sr_filter.inject_bell()
    assert out.getvalue() == "\a"

def test_header_formatting():
    assert format_header("=== Installation ===") == "*** Installation ***"
    assert format_header("--- Setup ---") == "*** Setup ***"
    assert format_header("## Steps ##") == "*** Steps ***"

def test_filter_write():
    out = StringIO()
    sr_filter = ScreenReaderFilter(out)
    sr_filter.write("Progress 50%\rProgress 100%\n")
    assert out.getvalue() == "Progress 50%\nProgress 100%\n"

def test_filter_getattr():
    out = StringIO()
    out.name = "<stdout>"
    sr_filter = ScreenReaderFilter(out)
    assert sr_filter.name == "<stdout>"
