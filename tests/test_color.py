import os
import sys
from unittest import mock
import pytest

from terminal_a11y.color import get_color_level, ColorLevel

class MockStream:
    def __init__(self, is_tty=True):
        self._is_tty = is_tty
        
    def isatty(self):
        return self._is_tty

@pytest.fixture
def clean_env():
    # Keep os.name as is, but clear environment variables that affect color
    with mock.patch.dict(os.environ, clear=True):
        yield

def test_no_color_env_var(clean_env):
    os.environ["NO_COLOR"] = "1"
    os.environ["COLORTERM"] = "truecolor"
    assert get_color_level(MockStream()) == ColorLevel.NONE

def test_no_color_empty_string_disables_color(clean_env):
    os.environ["NO_COLOR"] = ""
    os.environ["COLORTERM"] = "truecolor"
    assert get_color_level(MockStream()) == ColorLevel.NONE

def test_not_a_tty(clean_env):
    os.environ["COLORTERM"] = "truecolor"
    assert get_color_level(MockStream(is_tty=False)) == ColorLevel.NONE

def test_force_color_not_a_tty(clean_env):
    os.environ["FORCE_COLOR"] = "1"
    os.environ["COLORTERM"] = "truecolor"
    assert get_color_level(MockStream(is_tty=False)) == ColorLevel.TRUECOLOR

def test_windows_terminal(clean_env):
    os.environ["WT_SESSION"] = "some-guid"
    assert get_color_level(MockStream()) == ColorLevel.TRUECOLOR

def test_apple_terminal(clean_env):
    os.environ["TERM_PROGRAM"] = "Apple_Terminal"
    os.environ["TERM"] = "xterm-256color"
    assert get_color_level(MockStream()) == ColorLevel.TWO_FIFTY_SIX

def test_vte_terminal(clean_env):
    os.environ["VTE_VERSION"] = "3600"
    assert get_color_level(MockStream()) == ColorLevel.TRUECOLOR
    
def test_vte_terminal_old(clean_env):
    os.environ["VTE_VERSION"] = "3500"
    assert get_color_level(MockStream()) == ColorLevel.TWO_FIFTY_SIX

def test_256_color_term(clean_env):
    os.environ["TERM"] = "xterm-256color"
    assert get_color_level(MockStream()) == ColorLevel.TWO_FIFTY_SIX

def test_16_color_term(clean_env):
    os.environ["TERM"] = "xterm"
    assert get_color_level(MockStream()) == ColorLevel.SIXTEEN
