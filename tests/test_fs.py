"""Unit tests for reversec.common.fs."""

import hashlib

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


class TestHashing:
    # Regression coverage: md5sum/sha1sum previously looped forever because the
    # read loop compared bytes to the str literal "" (b"" != "" is always True
    # in Python 3), so the loop never terminated on any readable file.

    def test_md5sum_matches_hashlib(self, tmp_path):
        target = str(tmp_path / "data.bin")
        fs.write(target, b"hello world")
        assert fs.md5sum(target) == hashlib.md5(b"hello world").hexdigest()

    def test_sha1sum_matches_hashlib(self, tmp_path):
        target = str(tmp_path / "data.bin")
        fs.write(target, b"hello world")
        assert fs.sha1sum(target) == hashlib.sha1(b"hello world").hexdigest()

    def test_hashing_empty_file(self, tmp_path):
        target = str(tmp_path / "empty")
        fs.touch(target)
        assert fs.md5sum(target) == hashlib.md5(b"").hexdigest()

    def test_missing_file_returns_none(self, tmp_path):
        assert fs.md5sum(str(tmp_path / "nope")) is None
        assert fs.sha1sum(str(tmp_path / "nope")) is None
