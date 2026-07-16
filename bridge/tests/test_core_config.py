from __future__ import annotations

import json
from pathlib import Path
import tempfile
import textwrap
import unittest

from bridge.agent_deck_bridge.config import ConfigError, load_config
from bridge.agent_deck_bridge.core import (
    SessionObservation,
    SessionRegistry,
    normalize_state,
)
from bridge.agent_deck_bridge.protocol import (
    ActionCode,
    BatteryDisplayMode,
    NormalizedState,
)


class SessionRegistryTests(unittest.TestCase):
    def test_normalizes_all_public_states_and_unknown_to_disconnected(self) -> None:
        expected = {
            "idle": NormalizedState.IDLE,
            "working": NormalizedState.RUNNING,
            "waiting approval": NormalizedState.WAITING_APPROVAL,
            "waiting-input": NormalizedState.WAITING_INPUT,
            "done": NormalizedState.COMPLETED,
            "error": NormalizedState.FAILED,
            "unknown-new-value": NormalizedState.DISCONNECTED,
            None: NormalizedState.DISCONNECTED,
        }
        for raw, state in expected.items():
            with self.subTest(raw=raw):
                self.assertEqual(normalize_state(raw), state)

    def test_ids_are_stable_versions_increment_and_removed_ids_are_stale(self) -> None:
        registry = SessionRegistry(epoch=7)
        first = SessionObservation(
            "fixture",
            "a",
            "Alpha",
            "running",
            frozenset({ActionCode.INTERRUPT}),
        )
        second = SessionObservation("fixture", "b", "Beta", "idle")
        registry.refresh("fixture", [first, second], now=1)
        alpha, beta = registry.sessions
        registry.select(alpha.session_id)
        registry.refresh("fixture", [second, first], now=2)
        self.assertEqual(registry.selected_session_id, alpha.session_id)
        self.assertEqual(
            registry.get(alpha.session_id).state_version, alpha.state_version
        )
        changed = SessionObservation(
            "fixture",
            "a",
            "Alpha",
            "waiting_input",
            frozenset({ActionCode.INTERRUPT}),
        )
        registry.refresh("fixture", [changed], now=3)
        changed_alpha = registry.get(alpha.session_id)
        self.assertGreater(changed_alpha.state_version, alpha.state_version)
        self.assertIsNone(registry.get(beta.session_id))
        registry.refresh("fixture", [changed, second], now=4)
        new_beta = next(
            item for item in registry.sessions if item.upstream_id == "b"
        )
        self.assertNotEqual(new_beta.session_id, beta.session_id)

    def test_selection_clears_only_when_selected_session_disappears(self) -> None:
        registry = SessionRegistry(epoch=1)
        registry.refresh(
            "fixture",
            [
                SessionObservation("fixture", "a", "A", "idle"),
                SessionObservation("fixture", "b", "B", "idle"),
            ],
        )
        registry.select(registry.sessions[1].session_id)
        registry.refresh(
            "fixture", [SessionObservation("fixture", "a", "A", "idle")]
        )
        self.assertIsNone(registry.selected_session_id)


class ConfigTests(unittest.TestCase):
    def test_repository_yaml_example_loads_without_pyyaml(self) -> None:
        path = Path(__file__).parents[1] / "config.example.yaml"
        config = load_config(path)
        self.assertEqual(config.ptt_key_id, 11)
        self.assertEqual(config.brightness_percent, 20)
        self.assertEqual(
            config.battery_display_mode, BatteryDisplayMode.ON_CHANGE
        )
        self.assertEqual(
            config.safety_rules[ActionCode.APPROVE].required_state,
            NormalizedState.WAITING_APPROVAL,
        )
        self.assertIn(ActionCode.RUN_TESTS, config.safety_rules)
        self.assertIn(ActionCode.OPEN_DIFF, config.safety_rules)

    def test_json_toml_and_yaml_subset_are_supported(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            json_path = root / "config.json"
            json_path.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "device": {"brightness_percent": 33},
                    }
                ),
                encoding="utf-8",
            )
            self.assertEqual(load_config(json_path).brightness_percent, 33)

            toml_path = root / "config.toml"
            toml_path.write_text(
                "version = 1\n[device]\nbrightness_percent = 34\n",
                encoding="utf-8",
            )
            self.assertEqual(load_config(toml_path).brightness_percent, 34)

            yaml_path = root / "config.yaml"
            yaml_path.write_text(
                textwrap.dedent(
                    """
                    version: 1
                    device:
                      brightness_percent: 35
                      preferred_transports:
                        - usb_vendor_hid
                    """
                ),
                encoding="utf-8",
            )
            config = load_config(yaml_path)
            self.assertEqual(config.brightness_percent, 35)
            self.assertEqual(config.preferred_transports, ("usb_vendor_hid",))

    def test_dangerous_short_or_single_confirmation_configuration_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "unsafe.json"
            path.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "safety": {
                            "delete": {
                                "gesture": "short",
                                "require_second_confirmation": False,
                            }
                        },
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaises(ConfigError):
                load_config(path)

    def test_yaml_advanced_features_and_bad_indent_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.yaml"
            path.write_text("version: 1\ndevice: &defaults\n brightness_percent: 20\n")
            with self.assertRaises(ConfigError):
                load_config(path)

    def test_unknown_top_level_configuration_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "unknown.json"
            path.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "integrations": {"tmux": {"enabled": True}},
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaises(ConfigError):
                load_config(path)


if __name__ == "__main__":
    unittest.main()
