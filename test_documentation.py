#!/usr/bin/env python3
"""
Test suite for documentation changes related to issue #478
"""
import os
import re


def test_readme_contains_android10_note():
    """Verify README.md contains Android 10+ limitation note"""
    with open('README.md', 'r') as f:
        content = f.read()

    assert 'Android 10+ Background Execution Restrictions' in content, \
        "README should mention Android 10+ restrictions"
    assert 'TROUBLESHOOTING.md' in content, \
        "README should link to TROUBLESHOOTING.md"


def test_troubleshooting_file_exists():
    """Verify TROUBLESHOOTING.md exists and has proper structure"""
    assert os.path.exists('TROUBLESHOOTING.md'), \
        "TROUBLESHOOTING.md should exist"

    with open('TROUBLESHOOTING.md', 'r') as f:
        content = f.read()

    # Check for required sections
    assert '## Android 10+ Background Execution Limitations' in content, \
        "Should have Android 10+ section"
    assert '### Problem Description' in content, \
        "Should have problem description"
    assert '### Root Cause' in content, \
        "Should explain root cause"
    assert '### Workarounds' in content, \
        "Should provide workarounds"
    assert '### Future Solutions' in content, \
        "Should mention future solutions"

    # Check for important links
    assert 'https://developer.android.com/guide/components/activities/background-starts' in content, \
        "Should link to Android documentation"
    assert 'drozer-agent/pull/19' in content, \
        "Should reference PR #19"
    assert 'drozer/issues/478' in content or 'drozer/pull/478' in content or '#478' in content, \
        "Should reference issue #478"


def test_drozer_guide_contains_warning():
    """Verify drozer-guide.md contains Android 10+ warning in activity section"""
    with open('documentation/drozer-guide.md', 'r') as f:
        content = f.read()

    # Find the "Launching Activities" section
    activity_section_match = re.search(
        r'## 3\.4 Launching Activities.*?## 3\.5',
        content,
        re.DOTALL
    )

    assert activity_section_match, \
        "Should have section 3.4 Launching Activities"

    activity_section = activity_section_match.group(0)

    assert 'Android 10+' in activity_section, \
        "Activity section should mention Android 10+"
    assert 'TROUBLESHOOTING.md' in activity_section, \
        "Activity section should link to TROUBLESHOOTING.md"


def test_workarounds_are_actionable():
    """Verify workarounds section provides clear actionable steps"""
    with open('TROUBLESHOOTING.md', 'r') as f:
        content = f.read()

    # Extract workarounds section
    workarounds_match = re.search(
        r'### Workarounds(.*?)### Future Solutions',
        content,
        re.DOTALL
    )

    assert workarounds_match, "Should have Workarounds section"

    workarounds = workarounds_match.group(1)

    # Should have at least 3 options
    assert 'Option 1:' in workarounds, "Should have Option 1"
    assert 'Option 2:' in workarounds, "Should have Option 2"
    assert 'Option 3:' in workarounds, "Should have Option 3"

    # Options should have clear descriptions
    assert 'Keep Agent in Foreground' in workarounds, \
        "Option 1 should be about keeping agent in foreground"
    assert 'ADB' in workarounds or 'adb' in workarounds, \
        "Should mention ADB as alternative"


def test_links_use_correct_format():
    """Verify all markdown links use correct format"""
    with open('TROUBLESHOOTING.md', 'r') as f:
        content = f.read()

    # Check for broken link patterns
    # Links should be [text](url) not [text] (url) or [text](url )
    broken_links = re.findall(r'\]\s+\(', content)
    assert len(broken_links) == 0, \
        f"Found {len(broken_links)} links with space between ] and ("

    # Check that all section links use lowercase with hyphens
    section_links = re.findall(r'\[.*?\]\(#([^)]+)\)', content)
    for link in section_links:
        assert link.islower() or '-' in link, \
            f"Section link '{link}' should be lowercase with hyphens"


def test_all_referenced_issues_exist():
    """Verify all referenced GitHub issues/PRs are valid references"""
    with open('TROUBLESHOOTING.md', 'r') as f:
        content = f.read()

    # Should reference the main issue
    assert '#478' in content or 'issues/478' in content, \
        "Should reference issue #478"

    # Should reference related work
    assert 'drozer-agent' in content, \
        "Should mention drozer-agent repository"


if __name__ == '__main__':
    print("Running documentation validation tests...")

    tests = [
        test_readme_contains_android10_note,
        test_troubleshooting_file_exists,
        test_drozer_guide_contains_warning,
        test_workarounds_are_actionable,
        test_links_use_correct_format,
        test_all_referenced_issues_exist,
    ]

    failed = 0
    for test in tests:
        try:
            test()
            print(f"✓ {test.__name__}")
        except AssertionError as e:
            print(f"✗ {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test.__name__}: Unexpected error: {e}")
            failed += 1

    print(f"\n{len(tests) - failed}/{len(tests)} tests passed")
    exit(0 if failed == 0 else 1)
