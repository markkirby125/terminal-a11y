import platform
from unittest.mock import patch, MagicMock
import pytest
from terminal_a11y.audio import (
    MILESTONE_FREQUENCIES,
    play_tone,
    AudioProgress,
)


def test_milestone_frequencies_distinct():
    freqs = list(MILESTONE_FREQUENCIES.values())
    assert len(freqs) == len(set(freqs))


def test_play_tone_windows_uses_winsound():
    if platform.system() != "Windows":
        pytest.skip("Windows-only test")

    mock_winsound = MagicMock()
    with patch.dict("sys.modules", {"winsound": mock_winsound}):
        play_tone(440, 100)
        mock_winsound.Beep.assert_called_once_with(440, 100)


def test_play_tone_unix_no_crash():
    if platform.system() == "Windows":
        pytest.skip("Unix-only test")

    # Should not raise even if afplay/aplay are unavailable.
    result = play_tone(440, 50)
    assert isinstance(result, bool)


def test_audio_progress_reports_milestones():
    audio = AudioProgress()
    with patch("terminal_a11y.audio.play_tone") as mock_play:
        audio.report(25)
        audio.close()
        mock_play.assert_called_once()
        args = mock_play.call_args[0]
        assert args[0] == MILESTONE_FREQUENCIES[25]


def test_audio_progress_skips_already_reached():
    audio = AudioProgress()
    with patch("terminal_a11y.audio.play_tone") as mock_play:
        audio.report(30)
        audio.report(50)
        audio.close()
        assert mock_play.call_count == 2


def test_audio_progress_reset():
    audio = AudioProgress()
    with patch("terminal_a11y.audio.play_tone") as mock_play:
        audio.report(100)
        audio.reset()
        audio.report(100)
        audio.close()
        assert mock_play.call_count == 2
