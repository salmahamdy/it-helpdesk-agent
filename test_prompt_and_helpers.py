"""
Tests for agent/prompt.py and utils/helpers.py.

Run:  pytest tests/test_prompt_and_helpers.py -v
"""

import json
import pytest


# ===== Prompt Builder =====

class TestBuildPrompt:
    def test_includes_issue(self):
        from agent.prompt import build_prompt

        prompt = build_prompt("My printer is offline", [])
        assert "My printer is offline" in prompt

    def test_no_cases_no_rag_section(self):
        from agent.prompt import build_prompt

        prompt = build_prompt("Test issue", [])
        assert "SIMILAR RESOLVED CASES" not in prompt

    def test_includes_rag_context_legacy_format(self):
        from agent.prompt import build_prompt

        cases = [
            {
                "issue": "Printer not found",
                "resolution": "Restart spooler",
                "issue_class": "Hardware - Printer",
                "commands": ["net stop spooler"],
                "similarity_score": 0.82,
            }
        ]
        prompt = build_prompt("Printer issue", cases)

        assert "SIMILAR RESOLVED CASES" in prompt
        assert "Printer not found" in prompt
        assert "Restart spooler" in prompt
        assert "net stop spooler" in prompt
        assert "0.82" in prompt

    def test_includes_rag_context_os_dict_format(self):
        from agent.prompt import build_prompt

        cases = [
            {
                "issue": "WiFi not connecting",
                "resolution": {
                    "windows": "Flush DNS and reset adapter",
                    "mac": "Remove network from preferences",
                    "linux": "Restart NetworkManager",
                },
                "issue_class": "Network - WiFi",
                "commands": {
                    "windows": ["ipconfig /flushdns"],
                    "mac": ["sudo dscacheutil -flushcache"],
                    "linux": ["sudo systemctl restart NetworkManager"],
                },
                "similarity_score": 0.90,
            }
        ]
        # With OS specified → gets OS-specific resolution
        prompt = build_prompt("wifi issue", cases, os_info={"os": "Windows", "version": "11"})
        assert "Flush DNS and reset adapter" in prompt
        assert "ipconfig /flushdns" in prompt
        assert "NetworkManager" not in prompt

    def test_os_dict_format_mac(self):
        from agent.prompt import build_prompt

        cases = [
            {
                "issue": "No sound",
                "resolution": {"windows": "Restart audio service", "mac": "Kill coreaudiod", "linux": "Check PulseAudio"},
                "commands": {"windows": ["sndvol"], "mac": ["sudo killall coreaudiod"], "linux": ["pavucontrol"]},
                "issue_class": "Hardware - Audio",
                "similarity_score": 0.75,
            }
        ]
        prompt = build_prompt("no sound", cases, os_info={"os": "macOS", "version": "Sonoma 14.5"})
        assert "Kill coreaudiod" in prompt
        assert "sudo killall coreaudiod" in prompt

    def test_os_dict_format_linux(self):
        from agent.prompt import build_prompt

        cases = [
            {
                "issue": "No sound",
                "resolution": {"windows": "Restart audio service", "mac": "Kill coreaudiod", "linux": "Check PulseAudio"},
                "commands": {"windows": ["sndvol"], "mac": ["sudo killall coreaudiod"], "linux": ["pavucontrol"]},
                "issue_class": "Hardware - Audio",
                "similarity_score": 0.75,
            }
        ]
        prompt = build_prompt("no sound", cases, os_info={"os": "Linux", "version": "Ubuntu 24.04"})
        assert "Check PulseAudio" in prompt
        assert "pavucontrol" in prompt

    def test_os_dict_no_os_shows_all_variants(self):
        from agent.prompt import build_prompt

        cases = [
            {
                "issue": "Test",
                "resolution": {"windows": "Win fix", "mac": "Mac fix", "linux": "Linux fix"},
                "commands": {"windows": [], "mac": [], "linux": []},
                "issue_class": "Test",
                "similarity_score": 0.50,
            }
        ]
        prompt = build_prompt("test", cases)
        # Without os_info, all variants should appear
        assert "Win fix" in prompt
        assert "Mac fix" in prompt
        assert "Linux fix" in prompt

    def test_os_info_adds_system_context(self):
        from agent.prompt import build_prompt

        prompt = build_prompt("test issue", [], os_info={"os": "Windows", "version": "11 23H2"})
        assert "USER'S SYSTEM: Windows" in prompt
        assert "11 23H2" in prompt

    def test_no_os_info_no_system_context(self):
        from agent.prompt import build_prompt

        prompt = build_prompt("test issue", [])
        assert "USER'S SYSTEM" not in prompt

    def test_multiple_cases_numbered(self):
        from agent.prompt import build_prompt

        cases = [
            {"issue": "A", "resolution": "Fix A", "issue_class": "Cat A",
             "commands": [], "similarity_score": 0.9},
            {"issue": "B", "resolution": "Fix B", "issue_class": "Cat B",
             "commands": [], "similarity_score": 0.7},
        ]
        prompt = build_prompt("issue", cases)

        assert "Case 1" in prompt
        assert "Case 2" in prompt

    def test_prompt_requests_json(self):
        from agent.prompt import build_prompt

        prompt = build_prompt("test", [])
        assert "JSON" in prompt
        assert "issue_class" in prompt
        assert "confidence" in prompt
        assert "resolution_steps" in prompt

    def test_missing_optional_fields(self):
        """Cases with missing fields should not crash the prompt builder."""
        from agent.prompt import build_prompt

        cases = [{"issue": "Bare case"}]  # no resolution, commands, etc.
        prompt = build_prompt("test", cases)

        assert "Bare case" in prompt
        assert "N/A" in prompt  # default for missing resolution


class TestGetOsKey:
    def test_windows_variants(self):
        from agent.prompt import _get_os_key

        assert _get_os_key({"os": "Windows"}) == "windows"
        assert _get_os_key({"os": "windows"}) == "windows"
        assert _get_os_key({"os": "Win"}) == "windows"

    def test_mac_variants(self):
        from agent.prompt import _get_os_key

        assert _get_os_key({"os": "macOS"}) == "mac"
        assert _get_os_key({"os": "Mac"}) == "mac"
        assert _get_os_key({"os": "OSX"}) == "mac"

    def test_linux_variants(self):
        from agent.prompt import _get_os_key

        assert _get_os_key({"os": "Linux"}) == "linux"
        assert _get_os_key({"os": "Ubuntu"}) == "linux"
        assert _get_os_key({"os": "Fedora"}) == "linux"
        assert _get_os_key({"os": "Arch"}) == "linux"
        assert _get_os_key({"os": "Debian"}) == "linux"

    def test_unknown_os(self):
        from agent.prompt import _get_os_key

        assert _get_os_key({"os": "TempleOS"}) is None

    def test_none_input(self):
        from agent.prompt import _get_os_key

        assert _get_os_key(None) is None


class TestExtractOsField:
    def test_dict_format_with_matching_key(self):
        from agent.prompt import _extract_os_field

        case = {"resolution": {"windows": "Win fix", "mac": "Mac fix", "linux": "Linux fix"}}
        assert _extract_os_field(case, "resolution", "windows") == "Win fix"
        assert _extract_os_field(case, "resolution", "mac") == "Mac fix"
        assert _extract_os_field(case, "resolution", "linux") == "Linux fix"

    def test_dict_format_no_os_key(self):
        from agent.prompt import _extract_os_field

        case = {"resolution": {"windows": "Win fix", "mac": "Mac fix", "linux": "Linux fix"}}
        result = _extract_os_field(case, "resolution", None)
        assert "Win fix" in result
        assert "Mac fix" in result
        assert "Linux fix" in result

    def test_legacy_flat_string(self):
        from agent.prompt import _extract_os_field

        case = {"resolution": "Restart the service"}
        assert _extract_os_field(case, "resolution", "windows") == "Restart the service"

    def test_legacy_flat_commands(self):
        from agent.prompt import _extract_os_field

        case = {"commands": ["cmd1", "cmd2"]}
        assert _extract_os_field(case, "commands", "windows") == ["cmd1", "cmd2"]

    def test_missing_field_resolution(self):
        from agent.prompt import _extract_os_field

        assert _extract_os_field({}, "resolution", "windows") == "N/A"

    def test_missing_field_commands(self):
        from agent.prompt import _extract_os_field

        assert _extract_os_field({}, "commands", "windows") == []


# ===== Helpers =====

class TestConfidenceLabel:
    def test_high(self):
        from utils.helpers import confidence_label
        assert confidence_label(0.90) == "High"
        assert confidence_label(0.85) == "High"

    def test_medium(self):
        from utils.helpers import confidence_label
        assert confidence_label(0.70) == "Medium"
        assert confidence_label(0.60) == "Medium"

    def test_low(self):
        from utils.helpers import confidence_label
        assert confidence_label(0.50) == "Low"
        assert confidence_label(0.0) == "Low"


class TestConfidenceColor:
    def test_high_is_green(self):
        from utils.helpers import confidence_color
        assert confidence_color(0.90) == "#22c55e"

    def test_medium_is_amber(self):
        from utils.helpers import confidence_color
        assert confidence_color(0.70) == "#f59e0b"

    def test_low_is_red(self):
        from utils.helpers import confidence_color
        assert confidence_color(0.30) == "#ef4444"


class TestEscalationBadge:
    def test_required(self):
        from utils.helpers import escalation_badge
        badge = escalation_badge(True)
        assert "Escalation Required" in badge

    def test_not_required(self):
        from utils.helpers import escalation_badge
        badge = escalation_badge(False)
        assert "No Escalation" in badge


class TestFormatJsonDisplay:
    def test_formats_dict(self):
        from utils.helpers import format_json_display

        result = format_json_display({"a": 1, "b": [2, 3]})
        parsed = json.loads(result)
        assert parsed == {"a": 1, "b": [2, 3]}

    def test_indented(self):
        from utils.helpers import format_json_display

        result = format_json_display({"key": "value"})
        assert "\n" in result  # indented output has newlines
