# PC bridge architecture

The bridge converts unstable tool-specific observations into a stable device model and converts semantic device actions into state-checked tool commands.

## Proposed modules

```text
bridge/
  src/
    core/          # session registry, state normalization, selection
    policy/        # sensitive action authorization and confirmation
    protocol/      # shared envelope and messages
    transports/    # vendor HID, BLE GATT, WebSocket
    integrations/  # codex, hermes, omx, tmux
    config/        # validation, migrations, key mappings
    audit/         # structured guarded-action records
  tests/
    fixtures/
    integration/
    protocol/
```

Implementation language is deliberately not selected until a short spike compares USB HID, BLE, process watching, distribution, and testability on the primary host OS.

## Internal contracts

### Integration adapter

An integration adapter exposes:

- discover sessions
- poll or subscribe to session state
- read stable metadata and capabilities
- execute one semantic action against a stable session identifier
- return structured success, rejection, timeout, or unsupported results

Parsing CLI screen text is an adapter implementation detail and never becomes the device protocol.

### Session registry

The registry merges integration observations into:

- runtime-scoped numeric session ID
- integration kind and upstream identifier
- normalized state and state version
- label suitable for local logs/configuration
- supported semantic actions
- last observation and health

### Policy engine

The policy engine checks connection epoch, selected session, state version, supported action, configured gesture, and optional second confirmation. It records a structured audit event before and after execution.

### Transport adapter

USB Vendor HID, BLE GATT, and WebSocket adapters all emit/consume the envelope in `docs/protocol/device-protocol.md`. Reconnection always triggers capability negotiation and a complete snapshot.

## Configuration

See `config.example.yaml`. Real configuration and credentials stay outside the repository. Mappings refer to semantic actions, not shell snippets, for guarded operations.

## Integration priorities

1. tmux session discovery and selection.
2. A fixture-backed generic agent state source.
3. Codex integration with explicit version/capability detection.
4. OMX and Hermes adapters behind the same interface.
5. Optional Wi-Fi/WebSocket device transport.

## Safety rules

- A single short press cannot directly invoke push, deploy, delete, or approval unless an explicit reviewed policy allows it for a non-sensitive context.
- Shell commands use argument arrays or validated adapters; no device-supplied string is evaluated as a shell command.
- A transport reconnect cannot replay pending actions.
- A stale session or state version is rejected, not silently redirected to the new selection.
- Adapter failure yields `failed` or `unknown` health and does not crash the transport loop.
- K11 defaults to hold-to-talk: press starts host-side capture and release stops it. Disconnect, heartbeat expiry, bridge restart, or a configured maximum hold timeout must also stop capture.
- Push-to-talk is a semantic integration action, not an injected global hotkey. The bridge selects the supported Codex/host voice-input adapter and exposes a visible failure when none is available.
