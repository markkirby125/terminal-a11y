# Terminal Accessibility Layer (`terminal-a11y`)

A sensory enhancement layer providing `--screen-reader`, `--photophobia`, `--sensory-budget`, `--braille`, and `--audio-progress` modes for command-line utilities.

## The Problem

Modern command-line interfaces are intensely visual. Tools use 24-bit TrueColor styling, dynamic cursor positioning (`\r`), animated braille spinners, and visual progress bars.

- **Screen Readers Crash:** `\r` spinner loops overwrite lines 10–12 times a second, flooding NVDA, Orca, and VoiceOver speech queues. Color-only status indicators leave blind users with no semantic context.
- **Photophobia & Halation:** High-contrast pure white on black (`#FFFFFF` on `#000000`) causes severe optical halation for users with astigmatism. High-energy blue-cyan ANSI colors (450nm–480nm) strongly stimulate intrinsically photosensitive Retinal Ganglion Cells (ipRGCs), triggering trigeminal pain pathways and migraines.
- **Sensory Overload:** Verbose build logs and stack traces can flood users with thousands of lines of output in seconds.
- **Braille Display Mismatch:** Refreshable braille displays are typically 40 cells wide and cannot render emojis or complex Unicode symbols.

## The Solution

`terminal-a11y` introduces a cross-platform (Windows, macOS, Linux) stream filtering layer that mitigates these sensory barriers.

### `--screen-reader` (`--sr`)

- **Linearises Output:** Strips in-place line overwriting and visual spinners, emitting milestone-based text updates instead.
- **Audible Alerts:** Injects terminal bells (`\a`) on completion of long operations.
- **Semantic Text:** Translates color-only indicators into explicit `[PASS]`, `[FAIL]`, and `[INFO]` tokens.
- **Auto-Detection:** Automatically engages if `SCREEN_READER=1`, `CLAUDE_AX_SCREEN_READER=1`, or active OS screen readers are detected.

### `--photophobia` (`--soft`)

- **Amber Phosphor Emulation:** Maps neon ANSI colors to a photophysiologically calibrated amber palette (~590nm peak) and a soft charcoal background (`#120E04`).
- **Eliminates Halation:** Maintains crisp perceptual contrast without the bleeding fringe effect of `#FFFFFF`.
- **Migraine Safe:** Suppresses ipRGC activation by eliminating blue-cyan spikes.

### `--sensory-budget N`

- **Output Throttling:** Suppresses output after `N` lines (default 2000) and emits a single summary line such as `[Sensory budget] 543 lines suppressed to reduce overload.`
- **Prevents Flooding:** Keeps speech queues and braille displays manageable during long-running commands.

### `--braille`

- **40-Column Wrapping:** Hard-wraps all output to 40 characters so it fits refreshable braille displays.
- **ASCII Fallback:** Replaces emojis with `[emoji]`, unknown symbols with `[sym]`, and common glyphs like `✓`/`✗` with `[OK]`/`[X]`.

### `--audio-progress`

- **Non-Visual Cues:** Enqueues distinct tones at estimated progress milestones (25 %, 50 %, 75 %, 100 %) using native OS audio APIs (`winsound.Beep` on Windows, `afplay` on macOS, `aplay` on Linux). Tones are emitted as the output stream advances, not as precise temporal percentages.

### `--explain-errors`

- **Plain-Language Summaries:** Prefixes unhandled exceptions with an accessible explanation before the traceback, e.g. "The program tried to connect to another computer or service, but that service refused the connection."

## Installation

```bash
pip install terminal-a11y
```

## Usage

Wrap any noisy command:

```bash
terminal-a11y --screen-reader npm install
terminal-a11y --photophobia pytest
terminal-a11y --braille --screen-reader git log --oneline
terminal-a11y --audio-progress --screen-reader long-running-task
terminal-a11y --sensory-budget 500 --explain-errors -- pytest -v
```

When the wrapped command begins with a flag, separate it with `--`:

```bash
terminal-a11y --screen-reader -- my-tool --verbose
```

Or integrate into your Python CLI:

```python
from terminal_a11y import TerminalAccessibilityEngine

with TerminalAccessibilityEngine(
    screen_reader=True,   # or omit and set auto_detect=True
    photophobia=True,
    sensory_budget=1000,
    braille=True,
    audio_progress=True,
    explain_errors=True,
):
    # All subsequent sys.stdout / sys.stderr writes are filtered
    print("Loading...\rDone!")
```

## Development

```bash
git clone https://github.com/example/terminal-a11y.git
cd terminal-a11y
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e .
pip install pytest
```

### Running tests

```bash
python -m pytest -q
```

### Building the package

```bash
pip install build
python -m build
```

## API

- `terminal_a11y.TerminalAccessibilityEngine` — context manager that installs filters on `sys.stdout`/`sys.stderr`.
- `terminal_a11y.strip_ansi(text)` — remove ANSI escape sequences.
- `terminal_a11y.is_screen_reader_active()` — detect active screen readers via OS APIs and env vars.
- `terminal_a11y.get_color_level()` — resolve terminal color capability (`NO_COLOR`, `FORCE_COLOR`, `COLORTERM`, etc.).
- `terminal_a11y.track_progress(iterable)` — milestone-based progress reporter.

## Standards Compliance

- **WCAG2ICT:** Fulfills criteria 1.1.1 (Non-text Content), 1.3.2 (Meaningful Sequence), 1.4.1 (Use of Color), 1.4.3 (Contrast), 2.2.2 (Pause, Stop, Hide), and 4.1.3 (Status Messages).
- **NO_COLOR:** Strictly adheres to [no-color.org](https://no-color.org/) conventions.

## Contributing

Please see the issue tracker for open milestones. We use standard GitHub PR workflows.

## License

MIT License.
