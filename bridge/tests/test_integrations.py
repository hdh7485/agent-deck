from __future__ import annotations

import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from bridge.agent_deck_bridge.core import Session
from bridge.agent_deck_bridge.integrations import (
    CodexAdapter,
    FixtureAdapter,
    IntegrationError,
    TmuxAdapter,
)
from bridge.agent_deck_bridge.protocol import (
    ActionCode,
    ActionResultStatus,
    NormalizedState,
)


class FixtureAdapterTests(unittest.TestCase):
    def test_discovers_states_actions_and_simulates_results(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fixture.json"
            path.write_text(
                json.dumps(
                    {
                        "sessions": [
                            {
                                "id": "alpha",
                                "label": "Alpha",
                                "state": "waiting_approval",
                                "actions": ["approve", "reject"],
                                "metadata": {"model": "test"},
                            }
                        ],
                        "action_results": {
                            "alpha/approve": {
                                "status": "succeeded",
                                "detail": "approved",
                                "detail_code": 7,
                            }
                        },
                    }
                ),
                encoding="utf-8",
            )
            adapter = FixtureAdapter(path)
            observation = adapter.discover()[0]
            self.assertEqual(observation.state, "waiting_approval")
            session = Session(
                1,
                "fixture",
                "alpha",
                "Alpha",
                NormalizedState.WAITING_APPROVAL,
                1,
                observation.supported_actions,
                0,
            )
            result = adapter.execute(session, ActionCode.APPROVE)
            self.assertEqual(result.status, ActionResultStatus.SUCCEEDED)
            self.assertEqual(result.detail_code, 7)
            unsupported = adapter.execute(session, ActionCode.DELETE)
            self.assertEqual(unsupported.status, ActionResultStatus.UNSUPPORTED)

    def test_malformed_fixture_is_isolated_as_integration_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fixture.json"
            path.write_text('{"sessions": [{"id": 7}]}', encoding="utf-8")
            with self.assertRaises(IntegrationError):
                FixtureAdapter(path).discover()


class TmuxAdapterTests(unittest.TestCase):
    def test_uses_fixed_argv_and_never_a_shell(self) -> None:
        calls = []

        def runner(argv, timeout):
            calls.append((list(argv), timeout))
            return subprocess.CompletedProcess(
                argv,
                0,
                stdout=(
                    "%1\tdev\t0.0\tcodex\twaiting approval\t0\n"
                    "%2\tdev\t0.1\tzsh\tshell\t0\n"
                ),
                stderr="",
            )

        adapter = TmuxAdapter(executable="/safe/tmux", runner=runner)
        observations = adapter.discover()
        self.assertEqual(
            calls[0][0][:4], ["/safe/tmux", "list-panes", "-a", "-F"]
        )
        self.assertNotIn("send-keys", calls[0][0])
        self.assertEqual(
            observations[0].state, "waiting_approval"
        )
        self.assertEqual(observations[1].state, "idle")
        result = adapter.execute(
            Session(
                1,
                "tmux",
                "%1",
                "dev",
                NormalizedState.RUNNING,
                1,
                frozenset(),
                0,
            ),
            ActionCode.INTERRUPT,
        )
        self.assertEqual(result.status, ActionResultStatus.UNSUPPORTED)
        self.assertEqual(len(calls), 1)

    def test_no_server_is_an_empty_discovery(self) -> None:
        def runner(argv, timeout):
            return subprocess.CompletedProcess(
                argv, 1, stdout="", stderr="no server running on /tmp/tmux"
            )

        self.assertEqual(TmuxAdapter(runner=runner).discover(), [])


class CodexAdapterTests(unittest.TestCase):
    def test_capability_detection_only_runs_version_and_help(self) -> None:
        calls = []

        def runner(argv, timeout):
            calls.append(list(argv))
            if argv[-1] == "--version":
                return subprocess.CompletedProcess(
                    argv, 0, stdout="codex-cli 9.9\n", stderr=""
                )
            return subprocess.CompletedProcess(
                argv,
                0,
                stdout="resume exec --json approval sandbox voice\n",
                stderr="",
            )

        adapter = CodexAdapter(executable="/safe/codex", runner=runner)
        capabilities = adapter.detect_capabilities()
        self.assertTrue(capabilities.available)
        self.assertIn("voice_input", capabilities.capabilities)
        self.assertEqual(
            calls,
            [["/safe/codex", "--version"], ["/safe/codex", "--help"]],
        )
        result = adapter.execute(
            Session(
                1,
                "codex",
                "x",
                "Codex",
                NormalizedState.IDLE,
                1,
                frozenset(),
                0,
            ),
            ActionCode.DELETE,
        )
        self.assertEqual(result.status, ActionResultStatus.UNSUPPORTED)
        self.assertEqual(len(calls), 2)

    def test_missing_codex_is_reported_without_subprocess(self) -> None:
        adapter = CodexAdapter(which=lambda name: None)
        result = adapter.detect_capabilities()
        self.assertFalse(result.available)
        self.assertIsNone(result.executable)


if __name__ == "__main__":
    unittest.main()
