import sys
from io import StringIO
from unittest.mock import patch
import pytest
from terminal_a11y.cli import build_parser, run_wrapped, main


def test_build_parser_flags():
    parser = build_parser()
    args = parser.parse_args(["--screen-reader", "--photophobia", "--", "echo", "hi"])
    assert args.screen_reader is True
    assert args.photophobia is True
    assert args.command == ["echo", "hi"]


def test_run_wrapped_success():
    code = run_wrapped(["echo", "hello"], screen_reader=True)
    assert code == 0


def test_run_wrapped_command_not_found():
    code = run_wrapped(["definitely_not_a_real_command_12345"])
    assert code == 127


def test_run_wrapped_no_command():
    code = run_wrapped([])
    assert code == 2


def test_run_wrapped_with_braille():
    code = run_wrapped(["printf", "Status: %s\\n", "✓ done"], braille=True)
    assert code == 0


def test_main_requires_flag():
    with patch.object(sys, "stderr", new_callable=StringIO):
        code = main(["echo", "hello"])
        assert code == 2


def test_main_runs_command():
    code = main(["--screen-reader", "--", "echo", "hello"])
    assert code == 0


def test_main_auto_detect(capsys, monkeypatch):
    monkeypatch.setenv("SCREEN_READER", "1")
    code = main(["--auto", "--", "echo", "hello"])
    assert code == 0
