"""Unit tests for drozer.android.Intent (host-side logic only).

These cover the pure-Python behaviour of Intent that does not require a live
Android session: validity checks, default attributes and flag combination.
"""

import argparse

from drozer.android import Intent


class TestIntentValidity:

    def test_empty_intent_is_invalid(self):
        # An Intent must carry at least an action or a component.
        assert Intent().isValid() is False

    def test_action_makes_intent_valid(self):
        assert Intent(action="android.intent.action.VIEW").isValid() is True

    def test_component_makes_intent_valid(self):
        assert Intent(component=["com.example", "com.example.Activity"]).isValid() is True


class TestIntentDefaults:

    def test_attributes_default_to_none(self):
        intent = Intent()
        assert intent.action is None
        assert intent.category is None
        assert intent.component is None
        assert intent.data_uri is None
        assert intent.extras is None
        assert intent.flags is None
        assert intent.mimetype is None


class TestIntentFlags:

    # __build_flags is name-mangled; access it directly to unit-test the pure
    # flag-combination logic without needing a Java context.
    def _build(self, flags):
        return Intent()._Intent__build_flags(flags)

    def test_single_named_flag(self):
        assert self._build(["ACTIVITY_NEW_TASK"]) == 0x10000000

    def test_named_flags_are_ored_together(self):
        assert self._build(["ACTIVITY_NEW_TASK", "ACTIVITY_CLEAR_TOP"]) == 0x14000000

    def test_hexadecimal_flag(self):
        assert self._build(["0x10000000"]) == 0x10000000

    def test_empty_flag_list_is_zero(self):
        assert self._build([]) == 0x00000000


class TestIntentFromParser:

    def test_builds_intent_from_namespace(self):
        namespace = argparse.Namespace(
            action="android.intent.action.MAIN",
            category=None,
            component=None,
            data_uri=None,
            extras=[],
            flags=[],
            mimetype=None,
        )
        intent = Intent.fromParser(namespace)
        assert intent.action == "android.intent.action.MAIN"
        assert intent.isValid() is True
