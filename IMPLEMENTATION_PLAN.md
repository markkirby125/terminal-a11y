# terminal-a11y — Implementation Plan

## Overview
Terminal Accessibility Layer is a Python package providing `--screen-reader`, `--photophobia`, `--sensory-budget`, `--braille`, `--audio-progress`, and `--explain-errors` enhancement flags for command-line utilities. It addresses critical accessibility failures in modern CLIs, such as spinner-induced screen reader crashes, colour-only status indicators, halation from high-contrast terminal themes, sensory overload, and inaccessible progress cues.

## Scope Definition
### In Scope
- Cross-platform screen reader and TrueColor detection.
- ANSI escape sequence stripping and cursor control linearisation.
- Photophysiologically calibrated amber phosphor palette generation.
- Creative enhancements: Plain language error rewrites, sensory budget throttling, braille layout mode, and audio progress cues.
- Seamless Python integration via a stream filter or wrapper class.

### Out of Scope
- Web-based accessibility tooling or DOM manipulation.
- Direct integration with TUI frameworks like Textual (though compatibility is a goal).
- GUI screen reader APIs directly (we rely on terminal standard streams and platform env vars).

## Technical Architecture
The core architecture operates as an intercepting stream filter (`TerminalAccessibilityEngine`) wrapping `sys.stdout`. It processes outgoing text and events, applying sensory transformations based on active flags (`--screen-reader`, `--photophobia`) or detected environmental conditions (`NO_COLOR`, `CLAUDE_AX_SCREEN_READER`, OS-level AT APIs).

## File Map (every file the Python package will contain)
- `terminal_a11y/__init__.py`: Package entry point and API exports.
- `terminal_a11y/ansi.py`: Regex-based ANSI stripping and control character sanitisation.
- `terminal_a11y/detection.py`: Cross-platform screen reader (OS APIs, env vars) and TTY detection.
- `terminal_a11y/color.py`: TrueColor/256-color capability resolution and NO_COLOR compliance.
- `terminal_a11y/screen_reader.py`: Linearisation logic, status token conversion, and terminal bell injection.
- `terminal_a11y/photophobia.py`: Amber phosphor colour mapping and halation mitigation.
- `terminal_a11y/progress.py`: Milestone-based progress reporting replacing visual spinners.
- `terminal_a11y/errors.py`: Plain language error rewrites.
- `terminal_a11y/budget.py`: Sensory budget tracking and throttling logic.
- `terminal_a11y/braille.py`: 40-character line width reformatting and ASCII fallback.
- `terminal_a11y/audio.py`: Cross-platform native audio tone generation.
- `terminal_a11y/cli.py`: Shell wrapper entry point.
- `tests/test_ansi.py`: Unit tests for ANSI stripping.
- `tests/test_detection.py`: Tests for OS/env detection mechanisms.
- `tests/test_color.py`: Tests for capability resolution logic.
- `tests/test_screen_reader.py`: Tests for linearisation and token conversion.
- `tests/test_photophobia.py`: Tests for palette substitution.
- `tests/test_progress.py`: Tests for milestone-based progress reporting.
- `tests/test_errors.py`: Tests for plain-language error rewrites.
- `tests/test_budget.py`: Tests for sensory budget throttling.
- `tests/test_braille.py`: Tests for 40-column braille layout and ASCII fallback.
- `tests/test_audio.py`: Tests for cross-platform audio progress cues.
- `tests/test_cli.py`: Tests for the shell wrapper entry point.

## Implementation Phases
### Phase 1: ✅ ANSI Strip Engine
- **Goal:** Implement robust ECMA-48 / ISO 6429 control sequence stripping.
- **Files touched:** `terminal_a11y/ansi.py`, `tests/test_ansi.py`
- **Steps:** Define comprehensive regex pattern covering CSI, OSC, and C1 codes. Implement `strip_ansi` function.
- **Verification criteria:** Correctly removes complex 24-bit SGR codes, cursor positioning, and keeps visible text on Windows/macOS/Linux.

### Phase 2: ✅ Cross-Platform Screen Reader Detection
- **Goal:** Detect active assistive technology reliably.
- **Files touched:** `terminal_a11y/detection.py`, `tests/test_detection.py`
- **Steps:** Check env vars (`SCREEN_READER`, `TERM=dumb`). Implement Win32 `SystemParametersInfoW`, macOS `defaults read`, and Linux `gsettings` checks.
- **Verification criteria:** Returns True when NVDA (Windows), VoiceOver (macOS), or Orca (Linux) are active or simulated via env vars.

### Phase 3: ✅ Cross-Platform TrueColor Depth Detection
- **Goal:** Determine terminal color capabilities obeying `NO_COLOR` and `FORCE_COLOR`.
- **Files touched:** `terminal_a11y/color.py`, `tests/test_color.py`
- **Steps:** Check `NO_COLOR`, `FORCE_COLOR`, `isatty()`. Parse `COLORTERM`, `WT_SESSION`, and `TERM_PROGRAM` (especially Apple_Terminal limitation).
- **Verification criteria:** Returns `ColorLevel` (NONE, 16, 256, TRUECOLOR) accurately on Windows Terminal, ConHost, Apple Terminal, and VTE emulators.

### Phase 4: ✅ --screen-reader Flag (linearise, status tokens, bells, headers)
- **Goal:** Transform output to be screen-reader friendly.
- **Files touched:** `terminal_a11y/screen_reader.py`, `tests/test_screen_reader.py`
- **Steps:** Intercept writes, strip `\r` carriage returns, convert symbols to `[PASS]`/`[FAIL]`, inject `\a` bells on completion, format section headers.
- **Verification criteria:** Animated spinner inputs result in distinct, linear text outputs without buffer thrashing on all OSes.

### Phase 5: ✅ --photophobia Flag (amber palette, downsampling, NO_COLOR)
- **Goal:** Mitigate optical halation and ipRGC activation.
- **Files touched:** `terminal_a11y/photophobia.py`, `tests/test_photophobia.py`
- **Steps:** Define 24-bit, 256-color, and 16-color amber phosphor palettes. Map incoming colors to these safe palettes.
- **Verification criteria:** Output translates bright cyan/blue to 590nm amber equivalents. Disables completely if `NO_COLOR` is present (presence-only, per no-color.org).

### Phase 6: ✅ Milestone-Based Progress Reporter
- **Goal:** Provide accessible alternatives to visual progress bars.
- **Files touched:** `terminal_a11y/progress.py`
- **Steps:** Create a wrapper for progress tracking that emits text updates at 25%, 50%, 75%, and 100% instead of frame-by-frame redraws.
- **Verification criteria:** A loop of 100 iterations emits exactly 4 or 5 lines of text.

### Phase 7: ✅ Plain Language Error Rewriter (offline pattern matching)
- **Goal:** Clarify technical stack traces for accessibility.
- **Files touched:** `terminal_a11y/errors.py`, `tests/test_errors.py`
- **Steps:** Implement regex matchers for common exceptions (ConnectionRefused, PermissionError) and return plain English equivalents.
- **Verification criteria:** Unhandled standard exceptions print accessible summaries prefixing the trace.

### Phase 8: ✅ --sensory-budget Throttling
- **Goal:** Prevent sensory overload from excessive terminal output.
- **Files touched:** `terminal_a11y/budget.py`, `tests/test_budget.py`
- **Steps:** Track line count per session. Suppress output past threshold with a summary message.
- **Verification criteria:** Large text dumps (>2000 lines) truncate cleanly with a `[N lines suppressed]` warning.

### Phase 9: ✅ --braille Layout Mode
- **Goal:** Optimise output for refreshable braille displays.
- **Files touched:** `terminal_a11y/braille.py`, `tests/test_braille.py`
- **Steps:** Implement text wrapping at 40 characters. Strip emojis and unicode symbols, replacing them with ASCII equivalents.
- **Verification criteria:** Output never exceeds 40 columns and contains no unsupported glyphs.

### Phase 10: ✅ --audio-progress (cross-platform audio)
- **Goal:** Provide non-visual completion cues.
- **Files touched:** `terminal_a11y/audio.py`, `tests/test_audio.py`
- **Steps:** Use `winsound.Beep` (Windows), `afplay` (macOS), or `aplay` (Linux) to play distinct tones at progress milestones.
- **Verification criteria:** Distinct auditory tones play at 25/50/75/100 intervals on all three platforms.

### Phase 11: ✅ CLI Wrapper / Shell Integration
- **Goal:** Provide a standalone binary to wrap other tools.
- **Files touched:** `terminal_a11y/cli.py`, `tests/test_cli.py`
- **Steps:** Build an entry point using `argparse` to consume all accessibility flags, launching a subprocess with a PTY/pipe intercept and `--` separator support.
- **Verification criteria:** Running `terminal-a11y --screen-reader some_command` successfully filters its output.

### Phase 12: ✅ PyPI Packaging + README
- **Goal:** Release preparation.
- **Files touched:** `pyproject.toml`, `README.md`
- **Steps:** Finalise metadata, document API and shell wrapper usage, describe scientific rationale.
- **Verification criteria:** Package builds successfully via `python -m build` and installs correctly.

## GitHub Project Setup
### Labels
- `screen-reader`, `photophobia`, `ansi`, `no-color`, `nvda`, `orca`, `voiceover`, `amber-palette`, `audio`, `braille`, `cross-platform`, `a11y`, `bug`, `enhancement`
### Milestones
- `v0.1` (ANSI strip + SR detection)
- `v0.2` (--screen-reader + --photophobia flags)
- `v0.3` (sensory budget + audio + braille)
- `v1.0` (PyPI release)
### Issue Templates
- `bug_report.md`: OS, terminal emulator, screen reader, Python version, reproduction steps.
- `feature_request.md`: Use case, proposed solution, alternative solutions.
