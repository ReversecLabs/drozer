"""Unit tests for reversec.common.fs."""

from reversec.common import fs


class TestReadWrite:

    def test_write_then_read_round_trips(self, tmp_path):
        target = str(tmp_path / "data.bin")
        written = fs.write(target, b"hello world")
        assert written == len(b"hello world")
        assert fs.read(target) == b"hello world"

    def test_read_missing_file_returns_none(self, tmp_path):
        assert fs.read(str(tmp_path / "does-not-exist")) is None

    def test_read_as_text(self, tmp_path):
        target = str(tmp_path / "data.txt")
        fs.write(target, b"plain text")
        assert fs.read(target, "r") == "plain text"


class TestTouch:

    def test_touch_creates_empty_file(self, tmp_path):
        target = str(tmp_path / "touched")
        fs.touch(target)
        assert fs.read(target) == b""
