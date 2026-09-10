import pytest
from terminal_a11y.braille import (
    BRAILLE_WIDTH,
    ascii_fallback,
    wrap_braille,
    BrailleFilter,
)


def test_ascii_fallback_known_symbols():
    text = "Status: ✓ Success, ✗ Error, ⚠ Warning, ℹ Info"
    result = ascii_fallback(text)
    assert "[OK]" in result
    assert "[X]" in result
    assert "[!]" in result
    assert "[i]" in result
    assert "✓" not in result


def test_ascii_fallback_emoji_replacement():
    text = "Hello 🚀 world 🎉"
    result = ascii_fallback(text)
    assert "[emoji]" in result
    assert "🚀" not in result
    assert "🎉" not in result


def test_ascii_fallback_unknown_symbol():
    text = "Value: ☃"
    result = ascii_fallback(text)
    assert "[sym]" in result


def test_wrap_braille_respects_width():
    long_line = "a" * 100
    wrapped = wrap_braille(long_line)
    for line in wrapped.split("\n"):
        assert len(line) <= BRAILLE_WIDTH


def test_wrap_braille_word_boundary():
    text = "one two three four five six seven eight nine ten"
    wrapped = wrap_braille(text, width=20)
    for line in wrapped.split("\n"):
        assert len(line) <= 20


def test_wrap_braille_emoji_and_symbols():
    text = "Status: ✓ done 🚀"
    wrapped = wrap_braille(text)
    assert "[OK]" in wrapped
    assert "[emoji]" in wrapped
    assert all(len(line) <= BRAILLE_WIDTH for line in wrapped.split("\n"))


def test_braille_filter_buffers_and_flushes():
    from io import StringIO
    stream = StringIO()
    filt = BrailleFilter(stream)
    filt.write("hello world, this is a long line that exceeds forty characters")
    filt.flush()
    output = stream.getvalue()
    assert "hello world" in output
    for line in output.split("\n"):
        assert len(line) <= BRAILLE_WIDTH
