"""Unit tests for reversec.common.text."""

from reversec.common.text import indent, wrap


class TestIndent:

    def test_prefixes_every_line(self):
        assert indent("a\nb\nc", "  ") == "  a\n  b\n  c"

    def test_single_line(self):
        assert indent("hello", ">> ") == ">> hello"

    def test_empty_string_still_prefixed(self):
        assert indent("", ">") == ">"


class TestWrap:

    def test_text_shorter_than_width_is_unchanged(self):
        assert wrap("one two three", 1000) == "one two three"

    def test_wraps_on_word_boundaries(self):
        assert wrap("aaa bbb ccc", 5) == "aaa\nbbb\nccc"

    def test_existing_newlines_are_preserved(self):
        assert "\n" in wrap("first line\nsecond line", 1000)
