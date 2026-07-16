# Agent Deck PC bridge prototype

The bridge turns tool-specific observations into stable device state and turns
physical input into session-bound semantic intents. It is implemented with the
Python 3 standard library only.

This prototype is runnable and testable, but it deliberately does not yet open
a USB HID, BLE GATT, or WebSocket device transport. It also does not execute
tmux `send-keys`, arbitrary shell text, or destructive Codex commands. Those
backends require a separately reviewed transport/action implementation.

## Included

- Strict protocol v1 envelope and payload codec for every documented message
  type, including 64-byte USB HID padding and the 56-byte payload ceiling.
- Byte-exact firmware/bridge golden vectors.
- Runtime-scoped stable session IDs, monotonic state versions, selection, and
  normalized states.
- JSON fixture adapter for deterministic development.
- Read-only tmux pane discovery using a fixed argument array.
- Read-only Codex capability detection using only `--version` and `--help`.
- State-aware semantic action policy with connection epoch, selected session,
  state version, supported-action, gesture, hold-time, and optional second
  confirmation checks.
- Request-ID idempotency so a duplicate cannot execute an action twice.
- Fail-closed host push-to-talk lifecycle: release, selection change,
  disconnect, heartbeat expiry, and maximum-hold timeout all stop capture.
- Twelve-LED state snapshot generation.
- Initial `SET_BRIGHTNESS` generation from the configured brightness and current
  limit.
- JSON, TOML, and the documented YAML subset configuration loaders.
- Structured JSON-lines audit output.
- A CLI for validation, discovery, snapshots, decoding, capability detection,
  and bounded polling.

## Run

From the repository root:

```sh
python3 -m bridge.agent_deck_bridge \
  --config bridge/config.example.yaml \
  config-check

python3 -m bridge.agent_deck_bridge \
  --config bridge/config.example.yaml \
  discover --fixture bridge/fixtures/demo-sessions.json

python3 -m bridge.agent_deck_bridge \
  --config bridge/config.example.yaml \
  snapshot --fixture bridge/fixtures/demo-sessions.json

python3 -m bridge.agent_deck_bridge \
  decode 010300043412000004030201
```

The bounded runner emits one JSON state snapshot by default:

```sh
python3 -m bridge.agent_deck_bridge \
  --config bridge/config.example.yaml \
  run --fixture bridge/fixtures/demo-sessions.json --count 3 --interval 1
```

## Fixture format

```json
{
  "sessions": [
    {
      "id": "codex-main",
      "label": "Codex main",
      "state": "waiting_approval",
      "actions": ["approve", "reject", "push_to_talk"],
      "metadata": {"workspace": "agent-deck"}
    }
  ],
  "action_results": {
    "codex-main/approve": {
      "status": "succeeded",
      "detail": "fixture approval completed",
      "detail_code": 0
    }
  }
}
```

Fixture actions are simulations. Real action execution must be implemented
behind an integration adapter and remains subject to the same policy checks.

## Configuration

`config.example.yaml` uses a deliberately small YAML subset: nested mappings,
lists, booleans, null, numbers, and quoted or plain scalar strings. YAML tags,
anchors, merge keys, folded blocks, and inline objects are rejected. Use JSON
or TOML if richer syntax is needed.

Sensitive actions never accept a device-supplied command string. `push`,
`deploy`, and `delete` require a non-short gesture and two distinct confirmed
requests. Changing session, transport epoch, or state version invalidates the
pending confirmation.

`new_task` requires a long press by default. `run_tests`, `open_diff`, and
`set_reasoning_level` have explicit short-gesture policy rules, but they still
execute only when the selected integration advertises the action. Push-to-talk
uses the bounded K11 press/release path rather than `ACTION_INTENT`.

Read-only fixture, tmux, and Codex adapters are selected explicitly with the
CLI's `--fixture`, `--tmux`, and `--codex` options. Configuration does not
silently enable integrations.

Set `audit.path` to a path outside the repository to append guarded-action
JSON-lines records. Audit records contain semantic identifiers and outcomes,
not raw protocol payloads or credentials.

## Tests

```sh
python3 -m unittest discover -s bridge/tests -v
```

The suite covers all message golden vectors, malformed packets, enum and
length validation, sequence replay, state normalization, stable session IDs,
adapter isolation, safe subprocess argv, policy rejection paths, duplicate
request idempotency, confirmation cancellation, PTT fail-safe stops, LED
snapshots, configuration formats, and CLI smoke behavior.

## Module map

```text
bridge/agent_deck_bridge/
  protocol.py       envelope, payload schemas, sequence tracking
  core.py           session registry and state normalization
  integrations.py   fixture, tmux, and Codex adapters
  policy.py         semantic intent authorization and idempotency
  ptt.py            host capture lifecycle guard
  led.py            complete twelve-key LED snapshots
  runtime.py        adapter/policy/protocol orchestration
  config.py         JSON, TOML, and YAML-subset loading
  audit.py          structured audit sinks
  cli.py            runnable command-line surface
```
