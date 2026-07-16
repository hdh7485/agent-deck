"""Command-line entry point for the bridge prototype."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time
from typing import Sequence

from .audit import JsonLineAuditSink, NullAuditSink
from .config import ConfigError, load_config
from .integrations import CodexAdapter, FixtureAdapter, TmuxAdapter
from .protocol import Envelope, payload_to_dict
from .runtime import BridgeRuntime


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="agent-deck-bridge")
    parser.add_argument(
        "--config",
        default=str(Path(__file__).resolve().parents[1] / "config.example.yaml"),
        help="JSON, TOML, or supported YAML-subset configuration",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("config-check", help="validate configuration")

    discover = subparsers.add_parser("discover", help="discover sessions once")
    _adapter_arguments(discover)

    snapshot = subparsers.add_parser(
        "snapshot", help="emit a protocol STATE_SNAPSHOT envelope"
    )
    _adapter_arguments(snapshot)
    snapshot.add_argument("--hid-report", action="store_true")

    decode = subparsers.add_parser("decode", help="decode one envelope hex string")
    decode.add_argument("hex")

    capabilities = subparsers.add_parser(
        "codex-capabilities", help="run read-only Codex capability detection"
    )
    capabilities.add_argument("--codex-path")

    run = subparsers.add_parser(
        "run", help="poll adapters and emit JSON snapshots (no device transport)"
    )
    _adapter_arguments(run)
    run.add_argument("--interval", type=float, default=1.0)
    run.add_argument("--count", type=int, default=1)
    return parser


def _adapter_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--fixture")
    parser.add_argument("--tmux", action="store_true")
    parser.add_argument("--codex", action="store_true")


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "decode":
        return _decode(args.hex)
    if args.command == "codex-capabilities":
        adapter = CodexAdapter(executable=args.codex_path)
        print(json.dumps(_capability_dict(adapter), indent=2, sort_keys=True))
        return 0
    try:
        config = load_config(args.config)
    except ConfigError as error:
        print(f"configuration error: {error}", file=sys.stderr)
        return 2
    if args.command == "config-check":
        print(
            json.dumps(
                {
                    "valid": True,
                    "version": config.raw["version"],
                    "ptt_key_id": config.ptt_key_id,
                    "safety_actions": sorted(
                        action.name.lower() for action in config.safety_rules
                    ),
                },
                sort_keys=True,
            )
        )
        return 0

    adapters = []
    if args.fixture:
        adapters.append(FixtureAdapter(args.fixture))
    if args.tmux:
        adapters.append(TmuxAdapter())
    if args.codex:
        adapters.append(CodexAdapter())
    audit = (
        JsonLineAuditSink(config.audit_path)
        if config.audit_path
        else NullAuditSink()
    )
    runtime = BridgeRuntime(config, adapters, audit=audit)

    if args.command == "discover":
        sessions = runtime.poll()
        print(json.dumps([_session_dict(session) for session in sessions], indent=2))
        return 0
    if args.command == "snapshot":
        runtime.poll()
        _, _, snapshot = runtime.connect()
        print(snapshot.encode(hid_report=args.hid_report).hex())
        return 0
    if args.command == "run":
        if args.count < 1 or args.interval < 0:
            parser.error("--count must be positive and --interval non-negative")
        runtime.connect()
        for index in range(args.count):
            runtime.poll()
            snapshot = runtime.snapshot_envelope()
            print(
                json.dumps(
                    {
                        "wire_hex": snapshot.encode().hex(),
                        "payload": payload_to_dict(snapshot.decoded_payload()),
                    },
                    sort_keys=True,
                ),
                flush=True,
            )
            if index + 1 < args.count:
                time.sleep(args.interval)
        runtime.disconnect("cli_exit")
        return 0
    parser.error(f"unknown command {args.command}")
    return 2


def _decode(raw_hex: str) -> int:
    try:
        raw = bytes.fromhex(raw_hex)
        envelope = Envelope.decode(raw)
        payload = envelope.decoded_payload()
    except ValueError as error:
        print(f"decode error: {error}", file=sys.stderr)
        return 2
    print(
        json.dumps(
            {
                "major": envelope.major,
                "type": envelope.message_type.name.lower(),
                "flags": int(envelope.flags),
                "sequence": envelope.sequence,
                "request_id": envelope.request_id,
                "payload": payload_to_dict(payload),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def _capability_dict(adapter: CodexAdapter) -> dict[str, object]:
    capabilities = adapter.detect_capabilities()
    return {
        "available": capabilities.available,
        "executable": capabilities.executable,
        "version": capabilities.version,
        "capabilities": sorted(capabilities.capabilities),
        "error": capabilities.error,
    }


def _session_dict(session: object) -> dict[str, object]:
    return {
        "session_id": session.session_id,
        "integration": session.integration,
        "upstream_id": session.upstream_id,
        "label": session.label,
        "state": session.state.name.lower(),
        "state_version": session.state_version,
        "supported_actions": sorted(
            action.name.lower() for action in session.supported_actions
        ),
        "health": session.health,
    }


if __name__ == "__main__":
    raise SystemExit(main())
