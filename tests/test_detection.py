import os
import pytest
from unittest.mock import patch, MagicMock
from terminal_a11y.detection import is_screen_reader_active

@pytest.fixture
def clean_env():
    with patch.dict(os.environ, clear=True):
        yield

def test_env_var_screen_reader(clean_env):
    os.environ['SCREEN_READER'] = '1'
    assert is_screen_reader_active() is True

def test_env_var_term_dumb(clean_env):
    os.environ['TERM'] = 'dumb'
    assert is_screen_reader_active() is True

def test_env_var_claude_ax(clean_env):
    os.environ['CLAUDE_AX_SCREEN_READER'] = '1'
    assert is_screen_reader_active() is True
    
def test_env_var_false(clean_env):
    assert is_screen_reader_active() is False

@patch('platform.system', return_value='Windows')
def test_windows_screen_reader_active(mock_system, clean_env):
    class DummyBool:
        def __init__(self, val):
            self.value = val

    mock_ctypes = MagicMock()
    mock_ctypes.c_bool = DummyBool
    mock_ctypes.byref = lambda x: x

    def spi_mock(action, uiParam, pvParam, fWinIni):
        pvParam.value = True
        return 1

    mock_ctypes.windll.user32.SystemParametersInfoW = spi_mock

    with patch.dict('sys.modules', {'ctypes': mock_ctypes}):
        assert is_screen_reader_active() is True

@patch('platform.system', return_value='Windows')
def test_windows_screen_reader_inactive(mock_system, clean_env):
    class DummyBool:
        def __init__(self, val):
            self.value = val

    mock_ctypes = MagicMock()
    mock_ctypes.c_bool = DummyBool
    mock_ctypes.byref = lambda x: x

    def spi_mock(action, uiParam, pvParam, fWinIni):
        pvParam.value = False
        return 1

    mock_ctypes.windll.user32.SystemParametersInfoW = spi_mock

    with patch.dict('sys.modules', {'ctypes': mock_ctypes}):
        assert is_screen_reader_active() is False
        
@patch('platform.system', return_value='Darwin')
@patch('subprocess.run')
def test_macos_screen_reader_active(mock_run, mock_system, clean_env):
    mock_run.return_value = MagicMock(returncode=0, stdout='1\n')
    assert is_screen_reader_active() is True

@patch('platform.system', return_value='Darwin')
@patch('subprocess.run')
def test_macos_screen_reader_inactive(mock_run, mock_system, clean_env):
    mock_run.return_value = MagicMock(returncode=0, stdout='0\n')
    assert is_screen_reader_active() is False
    
@patch('platform.system', return_value='Darwin')
@patch('subprocess.run')
def test_macos_screen_reader_error(mock_run, mock_system, clean_env):
    mock_run.side_effect = Exception("Command failed")
    assert is_screen_reader_active() is False

@patch('platform.system', return_value='Linux')
@patch('subprocess.run')
def test_linux_screen_reader_active(mock_run, mock_system, clean_env):
    mock_run.return_value = MagicMock(returncode=0, stdout='true\n')
    assert is_screen_reader_active() is True

@patch('platform.system', return_value='Linux')
@patch('subprocess.run')
def test_linux_screen_reader_inactive(mock_run, mock_system, clean_env):
    mock_run.return_value = MagicMock(returncode=0, stdout='false\n')
    assert is_screen_reader_active() is False
