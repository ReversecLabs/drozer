"""Unit tests for drozer.util."""

import argparse

import pytest

from drozer.util import DefaultHost, DefaultPort, StoreZeroOrTwo, parse_server


class TestParseServer:

    def test_none_uses_defaults(self):
        host, port = parse_server(None)
        # DefaultHost ("localhost") is resolved to an address by parse_server.
        assert port == DefaultPort
        assert host  # a non-empty resolved address

    def test_host_only_uses_default_port(self):
        assert parse_server("127.0.0.1") == ("127.0.0.1", DefaultPort)

    def test_host_and_port(self):
        assert parse_server("10.0.0.5:9999") == ("10.0.0.5", 9999)

    def test_port_is_returned_as_int(self):
        _, port = parse_server("127.0.0.1:1234")
        assert isinstance(port, int) and port == 1234


class TestStoreZeroOrTwo:

    def _action(self):
        return StoreZeroOrTwo(option_strings=["--ssl"], dest="ssl")

    def test_accepts_zero_arguments(self):
        action, namespace = self._action(), argparse.Namespace()
        action(None, namespace, [], None)
        assert namespace.ssl == []

    def test_accepts_two_arguments(self):
        action, namespace = self._action(), argparse.Namespace()
        action(None, namespace, ["cert.pem", "key.pem"], None)
        assert namespace.ssl == ["cert.pem", "key.pem"]

    def test_rejects_one_argument(self):
        action, namespace = self._action(), argparse.Namespace()
        with pytest.raises(argparse.ArgumentTypeError):
            action(None, namespace, ["cert.pem"], None)
