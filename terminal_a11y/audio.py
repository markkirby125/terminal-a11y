import platform
import queue
import subprocess
import sys
import threading
from typing import Optional, Union

__all__ = ["MILESTONE_FREQUENCIES", "play_tone", "AudioProgress"]

# Distinct frequencies for progress milestones (Hz).
MILESTONE_FREQUENCIES = {
    25: 523,   # C5
    50: 659,   # E5
    75: 784,   # G5
    100: 1047, # C6
}

_DEFAULT_DURATION_MS = 200


def _beep_windows(frequency: int, duration_ms: int) -> bool:
    try:
        import winsound
        winsound.Beep(frequency, duration_ms)
        return True
    except Exception:
        return False


def _beep_unix(frequency: int, duration_ms: int) -> bool:
    """
    Generate a tone using a platform-specific external player.

    macOS uses ``afplay`` with a generated AIFF, Linux uses ``aplay``.
    Returns True if a tone was produced.
    """
    system = platform.system()
    sample_rate = 44100
    import math
    import struct

    # Generate a short PCM sine wave.
    num_samples = int(sample_rate * (duration_ms / 1000.0))
    samples = [
        int(32767 * 0.5 * math.sin(2 * math.pi * frequency * i / sample_rate))
        for i in range(num_samples)
    ]
    pcm_data = struct.pack("<" + "h" * num_samples, *samples)

    if system == "Darwin":
        # afplay only reads AIFF, so wrap the PCM in a minimal AIFF header.
        aiff = _pcm_to_aiff(pcm_data, sample_rate, 1, 16)
        try:
            proc = subprocess.run(
                ["afplay", "-"],
                input=aiff,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=5,
            )
            return proc.returncode == 0
        except Exception:
            return False

    if system == "Linux":
        try:
            proc = subprocess.run(
                ["aplay", "-q", "-t", "raw", "-f", "S16_LE", "-r", str(sample_rate), "-c", "1"],
                input=pcm_data,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=5,
            )
            return proc.returncode == 0
        except Exception:
            return False

    return False


def _pcm_to_aiff(pcm_data: bytes, sample_rate: int, channels: int, bits_per_sample: int) -> bytes:
    """Build a minimal uncompressed AIFF file from 16-bit mono PCM data."""
    import struct

    num_frames = len(pcm_data) // (channels * (bits_per_sample // 8))
    sample_rate_bytes = _sample_rate_to_extended(sample_rate)
    comm_chunk = struct.pack(">HHIH", channels, num_frames, bits_per_sample) + sample_rate_bytes

    ssnd_header = struct.pack(">II", 0, 0)  # offset, block size
    ssnd_chunk = b"SSND" + struct.pack(">I", 8 + len(pcm_data)) + ssnd_header + pcm_data
    comm_full = b"COMM" + struct.pack(">I", len(comm_chunk)) + comm_chunk
    form_data = comm_full + ssnd_chunk
    return b"FORM" + struct.pack(">I", 4 + len(form_data)) + b"AIFF" + form_data


def _sample_rate_to_extended(rate: int) -> bytes:
    """
    Convert an integer sample rate to an 80-bit IEEE 754 extended float.

    Supports common rates used in audio playback.
    """
    import math
    if rate == 0:
        return b"\x00" * 10

    sign = 0
    if rate < 0:
        sign = 1
        rate = -rate

    exponent = int(math.floor(math.log2(rate)))
    mantissa = rate / (2 ** exponent)
    # Extended precision: explicit integer bit (1), 63-bit fraction.
    biased_exp = exponent + 16383
    int_bit = 1
    fraction = int((mantissa - int_bit) * (2 ** 63))
    upper = (sign << 15) | (biased_exp & 0x7FFF)
    return (
        upper.to_bytes(2, "big")
        + ((1 << 63) | (fraction & ((1 << 63) - 1))).to_bytes(8, "big")
    )


def play_tone(frequency: int, duration_ms: int = _DEFAULT_DURATION_MS) -> bool:
    """
    Play a tone using the best native mechanism available on the current OS.

    Returns True if playback succeeded, False otherwise.
    """
    system = platform.system()
    if system == "Windows":
        return _beep_windows(frequency, duration_ms)
    if system in ("Darwin", "Linux"):
        return _beep_unix(frequency, duration_ms)
    return False


class AudioProgress:
    """
    Emits distinct audio tones at configured progress milestones.

    Tones are played sequentially on a single daemon worker thread so that
    overlapping ``report`` calls do not spawn an unbounded number of threads.
    """

    _SENTINEL: object = object()

    def __init__(
        self,
        milestones: Optional[dict[int, int]] = None,
        duration_ms: int = _DEFAULT_DURATION_MS,
    ):
        self.milestones = milestones or MILESTONE_FREQUENCIES.copy()
        self.duration_ms = duration_ms
        self._next_milestone_idx = 0
        self._sorted_milestones = sorted(self.milestones.keys())
        self._queue: "queue.Queue[Union[tuple[int, int], object]]" = queue.Queue()
        self._closed = False
        self._worker = threading.Thread(target=self._worker_loop, daemon=True)
        self._worker.start()

    def _worker_loop(self) -> None:
        while True:
            item = self._queue.get()
            if item is self._SENTINEL:
                self._queue.task_done()
                break
            freq, duration_ms = item  # type: ignore[misc]
            try:
                play_tone(freq, duration_ms)
            except Exception:
                # Best-effort audio; never crash the wrapped command.
                pass
            self._queue.task_done()

    def report(self, percent: int) -> None:
        """Enqueue the tone for the next reached milestone at or below ``percent``."""
        if self._closed:
            return
        if self._next_milestone_idx >= len(self._sorted_milestones):
            return
        milestone = self._sorted_milestones[self._next_milestone_idx]
        if percent >= milestone:
            freq = self.milestones.get(milestone, 440)
            self._queue.put((freq, self.duration_ms))
            self._next_milestone_idx += 1

    def reset(self) -> None:
        """Reset milestone tracking for a new run."""
        self._next_milestone_idx = 0

    def close(self) -> None:
        """Signal the worker thread to finish and wait for it to drain."""
        if self._closed:
            return
        self._closed = True
        self._queue.put(self._SENTINEL)
        self._worker.join(timeout=5.0)

    def __del__(self) -> None:
        self.close()
