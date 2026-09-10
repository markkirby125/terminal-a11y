import unittest
from terminal_a11y.ansi import strip_ansi

class TestAnsiStripping(unittest.TestCase):
    def test_strip_basic_colors(self):
        text = "\x1b[31mRed text\x1b[0m"
        self.assertEqual(strip_ansi(text), "Red text")

    def test_strip_24bit_colors(self):
        text = "\x1b[38;2;255;82;197mTruecolor\x1b[0m"
        self.assertEqual(strip_ansi(text), "Truecolor")

    def test_strip_cursor_positioning(self):
        text = "\x1b[2J\x1b[HHello\x1b[BWorld"
        self.assertEqual(strip_ansi(text), "HelloWorld")

    def test_strip_osc_titles(self):
        text = "\x1b]0;Window Title\x07Visible Text"
        self.assertEqual(strip_ansi(text), "Visible Text")

    def test_strip_mixed_sequences(self):
        text = "Start \x1b[1mBold\x1b[22m \x1b[32mGreen\x1b[39m End"
        self.assertEqual(strip_ansi(text), "Start Bold Green End")

    def test_no_ansi(self):
        text = "Plain text with no ANSI"
        self.assertEqual(strip_ansi(text), text)

if __name__ == '__main__':
    unittest.main()
