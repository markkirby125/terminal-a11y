import os
import platform
import subprocess

__all__ = ["is_screen_reader_active"]

def is_screen_reader_active() -> bool:
    """
    Detect if a screen reader or assistive technology is active.
    Checks environment variables first, then platform-specific APIs.
    """
    if os.environ.get('SCREEN_READER') == '1':
        return True
    if os.environ.get('TERM') == 'dumb':
        return True
    if os.environ.get('CLAUDE_AX_SCREEN_READER') == '1':
        return True
        
    system = platform.system()
    
    if system == 'Windows':
        try:
            import ctypes
            SPI_GETSCREENREADER = 0x0046
            is_active = ctypes.c_bool(False)
            result = ctypes.windll.user32.SystemParametersInfoW(
                SPI_GETSCREENREADER, 
                0, 
                ctypes.byref(is_active), 
                0
            )
            if result and is_active.value:
                return True
        except Exception:
            pass
            
    elif system == 'Darwin':
        try:
            result = subprocess.run(
                ['defaults', 'read', 'com.apple.universalaccess', 'voiceOverOnOffKey'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=1
            )
            if result.returncode == 0 and result.stdout.strip() == '1':
                return True
        except Exception:
            pass
            
    elif system == 'Linux':
        try:
            result = subprocess.run(
                ['gsettings', 'get', 'org.gnome.desktop.a11y.applications', 'screen-reader-enabled'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=1
            )
            if result.returncode == 0 and result.stdout.strip().lower() == 'true':
                return True
        except Exception:
            pass
            
    return False
