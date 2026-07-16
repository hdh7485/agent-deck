"""Dependency-free bridge configuration loading and validation."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import json
from pathlib import Path
import re
import tomllib
from typing import Any, Mapping

from .protocol import (
    ActionCode,
    BatteryDisplayMode,
    GestureClass,
    NormalizedState,
)


class ConfigError(ValueError):
    """Invalid bridge configuration."""


DEFAULT_CONFIG: dict[str, Any] = {
    "version": 1,
    "device": {
        "brightness_percent": 20,
        "heartbeat_timeout_ms": 3000,
        "preferred_transports": ["usb_vendor_hid", "ble_gatt"],
        "battery_display_mode": "on_change",
        "current_limit_ma": 300,
    },
    "controls": {
        "key_11": {
            "action": "push_to_talk",
            "activation": "hold",
            "max_hold_ms": 60000,
        }
    },
    "safety": {
        "approve": {
            "required_state": "waiting_approval",
            "gesture": "long",
            "minimum_hold_ms": 900,
        },
        "reject": {
            "required_state": "waiting_approval",
            "gesture": "double",
        },
        "interrupt": {
            "required_state": "running",
            "gesture": "long",
            "minimum_hold_ms": 700,
        },
        "push": {
            "gesture": "chord",
            "require_second_confirmation": True,
        },
        "deploy": {
            "gesture": "chord",
            "require_second_confirmation": True,
        },
        "delete": {
            "gesture": "chord",
            "require_second_confirmation": True,
        },
        "new_task": {
            "gesture": "long",
            "minimum_hold_ms": 500,
        },
        "run_tests": {
            "gesture": "short",
        },
        "open_diff": {
            "gesture": "short",
        },
        "set_reasoning_level": {
            "gesture": "short",
        },
    },
    "state_colors": {
        "idle": "#202020",
        "running": "#2D7FF9",
        "waiting_approval": "#FFB000",
        "waiting_input": "#8E5CFF",
        "completed": "#20B26B",
        "failed": "#E5484D",
        "disconnected": "#606060",
    },
    "audit": {"path": None},
}


@dataclass(frozen=True)
class SafetyRuleConfig:
    action: ActionCode
    required_state: NormalizedState | None
    gesture: GestureClass
    minimum_hold_ms: int
    require_second_confirmation: bool


@dataclass(frozen=True)
class BridgeConfig:
    raw: Mapping[str, Any]
    brightness_percent: int
    heartbeat_timeout_ms: int
    current_limit_ma: int
    battery_display_mode: BatteryDisplayMode
    preferred_transports: tuple[str, ...]
    ptt_key_id: int
    ptt_max_hold_ms: int
    safety_rules: Mapping[ActionCode, SafetyRuleConfig]
    state_colors: Mapping[NormalizedState, tuple[int, int, int]]
    audit_path: str | None


def load_config(path: str | Path | None = None) -> BridgeConfig:
    data = deepcopy(DEFAULT_CONFIG)
    if path is not None:
        config_path = Path(path)
        loaded = _read_config_file(config_path)
        if not isinstance(loaded, dict):
            raise ConfigError("configuration root must be a mapping")
        _deep_merge(data, loaded)
    return validate_config(data)


def validate_config(data: Mapping[str, Any]) -> BridgeConfig:
    unknown_top_level = set(data) - {
        "version",
        "device",
        "controls",
        "safety",
        "state_colors",
        "audit",
    }
    if unknown_top_level:
        names = ", ".join(sorted(str(item) for item in unknown_top_level))
        raise ConfigError(f"unknown top-level configuration keys: {names}")
    if data.get("version") != 1:
        raise ConfigError("only configuration version 1 is supported")
    device = _mapping(data, "device")
    brightness = _bounded_int(device, "brightness_percent", 0, 100)
    heartbeat_timeout_ms = _bounded_int(
        device, "heartbeat_timeout_ms", 250, 120000
    )
    current_limit_ma = _bounded_int(device, "current_limit_ma", 1, 5000)
    try:
        battery_display_mode = _enum_by_name(
            BatteryDisplayMode, device.get("battery_display_mode")
        )
    except KeyError as error:
        raise ConfigError("device.battery_display_mode is invalid") from error
    transports_raw = device.get("preferred_transports", [])
    if not isinstance(transports_raw, list) or not all(
        isinstance(item, str) and item for item in transports_raw
    ):
        raise ConfigError("device.preferred_transports must be a list of strings")

    controls = _mapping(data, "controls")
    ptt_entry: tuple[int, Mapping[str, Any]] | None = None
    for name, value in controls.items():
        if not isinstance(name, str) or not isinstance(value, Mapping):
            raise ConfigError("control entries must be named mappings")
        if value.get("action") == "push_to_talk":
            match = re.fullmatch(r"key_(\d+)", name)
            if match is None:
                raise ConfigError("push_to_talk control name must be key_<number>")
            if ptt_entry is not None:
                raise ConfigError("only one push_to_talk key may be configured")
            ptt_entry = (int(match.group(1)), value)
    if ptt_entry is None:
        raise ConfigError("a push_to_talk control is required")
    ptt_key_id, ptt_control = ptt_entry
    if ptt_control.get("activation") != "hold":
        raise ConfigError("push_to_talk activation must be hold")
    ptt_max_hold_ms = _bounded_int(ptt_control, "max_hold_ms", 1000, 300000)

    safety = _mapping(data, "safety")
    rules: dict[ActionCode, SafetyRuleConfig] = {}
    for action_name, rule_raw in safety.items():
        try:
            action = _enum_by_name(ActionCode, action_name)
        except KeyError as error:
            raise ConfigError(f"unknown safety action {action_name!r}") from error
        if not isinstance(rule_raw, Mapping):
            raise ConfigError(f"safety.{action_name} must be a mapping")
        state_raw = rule_raw.get("required_state")
        try:
            required_state = (
                _enum_by_name(NormalizedState, state_raw)
                if state_raw is not None
                else None
            )
        except KeyError as error:
            raise ConfigError(
                f"unknown required_state {state_raw!r} for {action_name}"
            ) from error
        gesture_raw = rule_raw.get("gesture")
        if not isinstance(gesture_raw, str):
            raise ConfigError(f"safety.{action_name}.gesture must be a string")
        try:
            gesture = _enum_by_name(GestureClass, gesture_raw)
        except KeyError as error:
            raise ConfigError(
                f"unknown gesture {gesture_raw!r} for {action_name}"
            ) from error
        minimum_hold_ms = rule_raw.get("minimum_hold_ms", 0)
        if not isinstance(minimum_hold_ms, int) or not 0 <= minimum_hold_ms <= 65535:
            raise ConfigError(
                f"safety.{action_name}.minimum_hold_ms must be 0..65535"
            )
        second = rule_raw.get("require_second_confirmation", False)
        if not isinstance(second, bool):
            raise ConfigError(
                f"safety.{action_name}.require_second_confirmation must be boolean"
            )
        if action in {ActionCode.PUSH, ActionCode.DEPLOY, ActionCode.DELETE}:
            if gesture is GestureClass.SHORT or not second:
                raise ConfigError(
                    f"{action_name} requires a non-short gesture and second confirmation"
                )
        rules[action] = SafetyRuleConfig(
            action,
            required_state,
            gesture,
            minimum_hold_ms,
            second,
        )

    color_map = _mapping(data, "state_colors")
    colors: dict[NormalizedState, tuple[int, int, int]] = {}
    for state in NormalizedState:
        key = state.name.lower()
        raw_color = color_map.get(key)
        if not isinstance(raw_color, str):
            raise ConfigError(f"state_colors.{key} must be a hex color")
        colors[state] = parse_color(raw_color)

    audit = _mapping(data, "audit")
    audit_path = audit.get("path")
    if audit_path is not None and not isinstance(audit_path, str):
        raise ConfigError("audit.path must be a string or null")

    return BridgeConfig(
        raw=data,
        brightness_percent=brightness,
        heartbeat_timeout_ms=heartbeat_timeout_ms,
        current_limit_ma=current_limit_ma,
        battery_display_mode=battery_display_mode,
        preferred_transports=tuple(transports_raw),
        ptt_key_id=ptt_key_id,
        ptt_max_hold_ms=ptt_max_hold_ms,
        safety_rules=rules,
        state_colors=colors,
        audit_path=audit_path,
    )


def parse_color(value: str) -> tuple[int, int, int]:
    if not re.fullmatch(r"#[0-9A-Fa-f]{6}", value):
        raise ConfigError(f"invalid RGB color {value!r}")
    return tuple(int(value[index : index + 2], 16) for index in (1, 3, 5))


def _read_config_file(path: Path) -> Any:
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as error:
        raise ConfigError(f"unable to read configuration: {error}") from error
    suffix = path.suffix.lower()
    try:
        if suffix == ".json":
            return json.loads(raw)
        if suffix == ".toml":
            return tomllib.loads(raw)
        if suffix in {".yaml", ".yml"}:
            return _parse_yaml_subset(raw)
    except (json.JSONDecodeError, tomllib.TOMLDecodeError, ValueError) as error:
        raise ConfigError(f"unable to parse {path.name}: {error}") from error
    raise ConfigError("configuration extension must be .json, .toml, .yaml, or .yml")


def _parse_yaml_subset(raw: str) -> Any:
    """Parse the mapping/list/scalar subset used by config.example.yaml.

    YAML anchors, tags, folded blocks, merge keys, and inline object syntax are
    intentionally unsupported. Configuration needing those features should use
    JSON or TOML instead.
    """

    tokens: list[tuple[int, str, int]] = []
    for line_number, raw_line in enumerate(raw.splitlines(), start=1):
        if "\t" in raw_line[: len(raw_line) - len(raw_line.lstrip())]:
            raise ValueError(f"line {line_number}: tabs are not allowed")
        content = _strip_yaml_comment(raw_line).rstrip()
        if not content.strip():
            continue
        indent = len(content) - len(content.lstrip(" "))
        if indent % 2:
            raise ValueError(f"line {line_number}: indentation must use two spaces")
        text = content.strip()
        if any(marker in text for marker in ("&", "*", "!!", "<<:")):
            raise ValueError(f"line {line_number}: advanced YAML features are disabled")
        tokens.append((indent, text, line_number))
    if not tokens:
        return {}

    def parse_block(index: int, indent: int) -> tuple[Any, int]:
        if index >= len(tokens) or tokens[index][0] != indent:
            raise ValueError("invalid indentation")
        is_list = tokens[index][1].startswith("- ")
        container: Any = [] if is_list else {}
        while index < len(tokens):
            token_indent, text, line_number = tokens[index]
            if token_indent < indent:
                break
            if token_indent > indent:
                raise ValueError(f"line {line_number}: unexpected indentation")
            if is_list:
                if not text.startswith("- "):
                    raise ValueError(f"line {line_number}: mixed list and mapping")
                item_text = text[2:].strip()
                if not item_text:
                    if index + 1 >= len(tokens) or tokens[index + 1][0] <= indent:
                        raise ValueError(f"line {line_number}: empty list item")
                    item, index = parse_block(index + 1, tokens[index + 1][0])
                    container.append(item)
                    continue
                container.append(_parse_scalar(item_text))
                index += 1
                continue

            if text.startswith("- "):
                raise ValueError(f"line {line_number}: mixed mapping and list")
            if ":" not in text:
                raise ValueError(f"line {line_number}: expected key: value")
            key, value_text = text.split(":", 1)
            key = key.strip()
            if not re.fullmatch(r"[A-Za-z0-9_-]+", key):
                raise ValueError(f"line {line_number}: invalid key {key!r}")
            if key in container:
                raise ValueError(f"line {line_number}: duplicate key {key!r}")
            value_text = value_text.strip()
            if value_text:
                container[key] = _parse_scalar(value_text)
                index += 1
                continue
            if index + 1 >= len(tokens) or tokens[index + 1][0] <= indent:
                container[key] = {}
                index += 1
                continue
            child_indent = tokens[index + 1][0]
            if child_indent != indent + 2:
                raise ValueError(
                    f"line {tokens[index + 1][2]}: nested indentation must increase by two"
                )
            child, index = parse_block(index + 1, child_indent)
            container[key] = child
        return container, index

    parsed, final_index = parse_block(0, tokens[0][0])
    if tokens[0][0] != 0 or final_index != len(tokens):
        raise ValueError("invalid YAML document structure")
    return parsed


def _strip_yaml_comment(line: str) -> str:
    quote: str | None = None
    escaped = False
    for index, character in enumerate(line):
        if escaped:
            escaped = False
            continue
        if character == "\\" and quote == '"':
            escaped = True
            continue
        if character in {"'", '"'}:
            if quote is None:
                quote = character
            elif quote == character:
                quote = None
            continue
        if character == "#" and quote is None:
            if index == 0 or line[index - 1].isspace():
                return line[:index]
    return line


def _parse_scalar(text: str) -> Any:
    lowered = text.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    if lowered in {"null", "~"}:
        return None
    if text.startswith(("{", "[", ">", "|")):
        raise ValueError("inline objects and block scalars are not supported")
    if text.startswith(('"', "'")):
        if len(text) < 2 or text[-1] != text[0]:
            raise ValueError("unterminated quoted scalar")
        if text[0] == '"':
            return json.loads(text)
        return text[1:-1].replace("''", "'")
    if re.fullmatch(r"[-+]?\d+", text):
        return int(text)
    if re.fullmatch(r"[-+]?(?:\d+\.\d*|\d*\.\d+)", text):
        return float(text)
    return text


def _deep_merge(target: dict[str, Any], incoming: Mapping[str, Any]) -> None:
    for key, value in incoming.items():
        if (
            key in target
            and isinstance(target[key], dict)
            and isinstance(value, Mapping)
        ):
            _deep_merge(target[key], value)
        else:
            target[key] = deepcopy(value)


def _mapping(data: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    value = data.get(key)
    if not isinstance(value, Mapping):
        raise ConfigError(f"{key} must be a mapping")
    return value


def _bounded_int(
    data: Mapping[str, Any], key: str, minimum: int, maximum: int
) -> int:
    value = data.get(key)
    if not isinstance(value, int) or isinstance(value, bool):
        raise ConfigError(f"{key} must be an integer")
    if not minimum <= value <= maximum:
        raise ConfigError(f"{key} must be {minimum}..{maximum}")
    return value


def _enum_by_name(enum_type: type[Any], name: Any) -> Any:
    if not isinstance(name, str):
        raise KeyError(name)
    normalized = name.strip().upper().replace("-", "_").replace(" ", "_")
    if enum_type is GestureClass:
        normalized = {
            "SHORT_PRESS": "SHORT",
            "LONG_PRESS": "LONG",
            "DOUBLE_PRESS": "DOUBLE",
        }.get(normalized, normalized)
    return enum_type[normalized]
