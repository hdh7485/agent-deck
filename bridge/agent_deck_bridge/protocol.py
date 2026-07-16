"""Transport-independent Agent Deck protocol v1 codec.

The codec deliberately rejects unknown enums, reserved flag bits, non-zero USB
padding, and payloads that do not exactly match their message schema. This
keeps malformed device input away from the policy and integration layers.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from enum import IntEnum, IntFlag
import struct
from typing import Any, ClassVar, Mapping


PROTOCOL_MAJOR = 1
HEADER_SIZE = 8
MAX_PAYLOAD = 56
HID_REPORT_SIZE = 64


class ProtocolError(ValueError):
    """Base protocol validation error."""


class EnvelopeError(ProtocolError):
    """Invalid envelope or transport framing."""


class PayloadError(ProtocolError):
    """Invalid message payload."""


class SequenceError(ProtocolError):
    """Duplicate or stale sequence number."""


class MessageType(IntEnum):
    HELLO = 0x01
    HELLO_ACK = 0x02
    HEARTBEAT = 0x03
    ACK = 0x04
    STATE_SNAPSHOT = 0x10
    SET_AGENT_STATE = 0x11
    SET_SELECTED_AGENT = 0x12
    SET_LED = 0x13
    SET_BRIGHTNESS = 0x14
    SET_MODE = 0x15
    ACTION_RESULT = 0x16
    SET_BATTERY_DISPLAY_MODE = 0x17
    KEY_EVENT = 0x20
    ENCODER_DELTA = 0x21
    ENCODER_CLICK = 0x22
    JOYSTICK_EVENT = 0x23
    TOUCH_EVENT = 0x24
    DEVICE_STATUS = 0x25
    BATTERY_LEVEL = 0x26
    ACTION_INTENT = 0x27


class EnvelopeFlag(IntFlag):
    NONE = 0
    ACK_REQUIRED = 1 << 0
    RESPONSE = 1 << 1
    ERROR = 1 << 2


KNOWN_FLAGS = EnvelopeFlag.ACK_REQUIRED | EnvelopeFlag.RESPONSE | EnvelopeFlag.ERROR


class ImplementationId(IntEnum):
    UNKNOWN = 0
    BRIDGE = 1
    ESP32_S3 = 2
    NRF52840 = 3


class AckStatus(IntEnum):
    OK = 0
    REJECTED = 1
    MALFORMED = 2
    UNSUPPORTED = 3
    STALE = 4
    CONFLICT = 5


class NormalizedState(IntEnum):
    IDLE = 0
    RUNNING = 1
    WAITING_APPROVAL = 2
    WAITING_INPUT = 3
    COMPLETED = 4
    FAILED = 5
    DISCONNECTED = 6


class ModeCode(IntEnum):
    DEFAULT = 0
    SESSION_SELECT = 1
    ACTION_CONFIRM = 2
    BATTERY = 3


class BatteryDisplayMode(IntEnum):
    NEVER = 0
    ON_CHANGE = 1
    ALWAYS = 2


class EventEdge(IntEnum):
    RELEASE = 0
    PRESS = 1


class JoystickDirection(IntEnum):
    CENTER = 0
    UP = 1
    RIGHT = 2
    DOWN = 3
    LEFT = 4


class TouchGesture(IntEnum):
    PRESS = 0
    RELEASE = 1
    TAP = 2
    DOUBLE_TAP = 3
    LONG_PRESS = 4


class GestureClass(IntEnum):
    SHORT = 1
    LONG = 2
    DOUBLE = 3
    CHORD = 4


class ActionCode(IntEnum):
    APPROVE = 1
    REJECT = 2
    INTERRUPT = 3
    PUSH = 4
    DEPLOY = 5
    DELETE = 6
    NEW_TASK = 7
    RUN_TESTS = 8
    OPEN_DIFF = 9
    SET_REASONING_LEVEL = 10
    PUSH_TO_TALK = 11


class ActionResultStatus(IntEnum):
    SUCCEEDED = 0
    REJECTED = 1
    TIMEOUT = 2
    UNSUPPORTED = 3
    CONFIRMATION_REQUIRED = 4
    FAILED = 5


class TransportCode(IntEnum):
    UNKNOWN = 0
    USB_VENDOR_HID = 1
    BLE_GATT = 2
    WEBSOCKET = 3


class AdapterCode(IntEnum):
    UNKNOWN = 0
    ESP32_S3 = 1
    NRF52840 = 2


@dataclass(frozen=True)
class HelloPayload:
    implementation_id: ImplementationId
    minor: int
    max_payload: int
    capabilities: int
    epoch: int


@dataclass(frozen=True)
class HelloAckPayload:
    status: AckStatus
    minor: int
    max_payload: int
    capabilities: int
    epoch: int


@dataclass(frozen=True)
class HeartbeatPayload:
    uptime_ms: int


@dataclass(frozen=True)
class AckPayload:
    acknowledged_type: MessageType
    status: AckStatus
    detail: int = 0


@dataclass(frozen=True)
class StateSnapshotPayload:
    epoch: int
    selected_session_id: int
    state_version: int
    brightness_percent: int
    mode: ModeCode
    battery_display_mode: BatteryDisplayMode
    leds: tuple[tuple[int, int, int], ...]


@dataclass(frozen=True)
class SetAgentStatePayload:
    session_id: int
    state_version: int
    state: NormalizedState


@dataclass(frozen=True)
class SetSelectedAgentPayload:
    session_id: int
    state_version: int


@dataclass(frozen=True)
class SetLedPayload:
    index: int
    red: int
    green: int
    blue: int
    expiry_ms: int


@dataclass(frozen=True)
class SetBrightnessPayload:
    brightness_percent: int
    current_limit_ma: int


@dataclass(frozen=True)
class SetModePayload:
    mode: ModeCode


@dataclass(frozen=True)
class ActionResultPayload:
    action: ActionCode
    status: ActionResultStatus
    detail: int = 0


@dataclass(frozen=True)
class SetBatteryDisplayModePayload:
    mode: BatteryDisplayMode


@dataclass(frozen=True)
class KeyEventPayload:
    key_id: int
    edge: EventEdge
    duration_ms: int
    modifiers: int = 0


@dataclass(frozen=True)
class EncoderDeltaPayload:
    delta: int
    acceleration: int = 0


@dataclass(frozen=True)
class EncoderClickPayload:
    edge: EventEdge
    duration_ms: int


@dataclass(frozen=True)
class JoystickEventPayload:
    direction: JoystickDirection
    edge: EventEdge
    duration_ms: int


@dataclass(frozen=True)
class TouchEventPayload:
    gesture: TouchGesture
    duration_ms: int


@dataclass(frozen=True)
class DeviceStatusPayload:
    firmware_major: int
    firmware_minor: int
    adapter: AdapterCode
    transport: TransportCode
    fault_flags: int


@dataclass(frozen=True)
class BatteryLevelPayload:
    millivolts: int
    percent: int
    flags: int


@dataclass(frozen=True)
class ActionIntentPayload:
    epoch: int
    session_id: int
    state_version: int
    action: ActionCode
    gesture: GestureClass
    hold_ms: int


Payload = (
    HelloPayload
    | HelloAckPayload
    | HeartbeatPayload
    | AckPayload
    | StateSnapshotPayload
    | SetAgentStatePayload
    | SetSelectedAgentPayload
    | SetLedPayload
    | SetBrightnessPayload
    | SetModePayload
    | ActionResultPayload
    | SetBatteryDisplayModePayload
    | KeyEventPayload
    | EncoderDeltaPayload
    | EncoderClickPayload
    | JoystickEventPayload
    | TouchEventPayload
    | DeviceStatusPayload
    | BatteryLevelPayload
    | ActionIntentPayload
)


@dataclass(frozen=True)
class _FixedSpec:
    payload_type: type[Any]
    format: str
    enum_fields: Mapping[str, type[IntEnum]]


_FIXED_SPECS: dict[MessageType, _FixedSpec] = {
    MessageType.HELLO: _FixedSpec(
        HelloPayload, "<BBHII", {"implementation_id": ImplementationId}
    ),
    MessageType.HELLO_ACK: _FixedSpec(
        HelloAckPayload, "<BBHII", {"status": AckStatus}
    ),
    MessageType.HEARTBEAT: _FixedSpec(HeartbeatPayload, "<I", {}),
    MessageType.ACK: _FixedSpec(
        AckPayload,
        "<BBH",
        {"acknowledged_type": MessageType, "status": AckStatus},
    ),
    MessageType.SET_AGENT_STATE: _FixedSpec(
        SetAgentStatePayload, "<IIB", {"state": NormalizedState}
    ),
    MessageType.SET_SELECTED_AGENT: _FixedSpec(
        SetSelectedAgentPayload, "<II", {}
    ),
    MessageType.SET_LED: _FixedSpec(SetLedPayload, "<BBBBH", {}),
    MessageType.SET_BRIGHTNESS: _FixedSpec(
        SetBrightnessPayload, "<BH", {}
    ),
    MessageType.SET_MODE: _FixedSpec(
        SetModePayload, "<B", {"mode": ModeCode}
    ),
    MessageType.ACTION_RESULT: _FixedSpec(
        ActionResultPayload,
        "<BBH",
        {"action": ActionCode, "status": ActionResultStatus},
    ),
    MessageType.SET_BATTERY_DISPLAY_MODE: _FixedSpec(
        SetBatteryDisplayModePayload, "<B", {"mode": BatteryDisplayMode}
    ),
    MessageType.KEY_EVENT: _FixedSpec(
        KeyEventPayload, "<BBHB", {"edge": EventEdge}
    ),
    MessageType.ENCODER_DELTA: _FixedSpec(
        EncoderDeltaPayload, "<hB", {}
    ),
    MessageType.ENCODER_CLICK: _FixedSpec(
        EncoderClickPayload, "<BH", {"edge": EventEdge}
    ),
    MessageType.JOYSTICK_EVENT: _FixedSpec(
        JoystickEventPayload,
        "<BBH",
        {"direction": JoystickDirection, "edge": EventEdge},
    ),
    MessageType.TOUCH_EVENT: _FixedSpec(
        TouchEventPayload, "<BH", {"gesture": TouchGesture}
    ),
    MessageType.DEVICE_STATUS: _FixedSpec(
        DeviceStatusPayload,
        "<BBBBI",
        {"adapter": AdapterCode, "transport": TransportCode},
    ),
    MessageType.BATTERY_LEVEL: _FixedSpec(
        BatteryLevelPayload, "<HBB", {}
    ),
    MessageType.ACTION_INTENT: _FixedSpec(
        ActionIntentPayload,
        "<IIIBBH",
        {"action": ActionCode, "gesture": GestureClass},
    ),
}


_PAYLOAD_TYPE_BY_MESSAGE: dict[MessageType, type[Any]] = {
    **{message_type: spec.payload_type for message_type, spec in _FIXED_SPECS.items()},
    MessageType.STATE_SNAPSHOT: StateSnapshotPayload,
}


def _validate_u8(value: int, name: str) -> None:
    if not 0 <= value <= 0xFF:
        raise PayloadError(f"{name} must fit uint8")


def _validate_u16(value: int, name: str) -> None:
    if not 0 <= value <= 0xFFFF:
        raise PayloadError(f"{name} must fit uint16")


def _validate_u32(value: int, name: str) -> None:
    if not 0 <= value <= 0xFFFFFFFF:
        raise PayloadError(f"{name} must fit uint32")


def _validate_common(message_type: MessageType, payload: Payload) -> None:
    expected = _PAYLOAD_TYPE_BY_MESSAGE.get(message_type)
    if expected is None:
        raise PayloadError(f"no payload schema for {message_type.name}")
    if not isinstance(payload, expected):
        raise PayloadError(
            f"{message_type.name} requires {expected.__name__}, "
            f"got {type(payload).__name__}"
        )


def _validate_payload(message_type: MessageType, payload: Payload) -> None:
    _validate_common(message_type, payload)
    if isinstance(payload, (HelloPayload, HelloAckPayload)):
        _validate_u8(payload.minor, "minor")
        _validate_u16(payload.max_payload, "max_payload")
        if payload.max_payload > MAX_PAYLOAD:
            raise PayloadError("max_payload exceeds protocol v1 limit")
        _validate_u32(payload.capabilities, "capabilities")
        _validate_u32(payload.epoch, "epoch")
    elif isinstance(payload, HeartbeatPayload):
        _validate_u32(payload.uptime_ms, "uptime_ms")
    elif isinstance(payload, AckPayload):
        _validate_u16(payload.detail, "detail")
    elif isinstance(payload, StateSnapshotPayload):
        _validate_u32(payload.epoch, "epoch")
        _validate_u32(payload.selected_session_id, "selected_session_id")
        _validate_u32(payload.state_version, "state_version")
        if not 0 <= payload.brightness_percent <= 100:
            raise PayloadError("brightness_percent must be 0..100")
        if len(payload.leds) > 12:
            raise PayloadError("STATE_SNAPSHOT supports at most 12 LEDs")
        for color in payload.leds:
            if len(color) != 3:
                raise PayloadError("each LED color must have three channels")
            for channel in color:
                _validate_u8(channel, "LED channel")
    elif isinstance(payload, SetAgentStatePayload):
        _validate_u32(payload.session_id, "session_id")
        _validate_u32(payload.state_version, "state_version")
    elif isinstance(payload, SetSelectedAgentPayload):
        _validate_u32(payload.session_id, "session_id")
        _validate_u32(payload.state_version, "state_version")
    elif isinstance(payload, SetLedPayload):
        for name in ("index", "red", "green", "blue"):
            _validate_u8(getattr(payload, name), name)
        _validate_u16(payload.expiry_ms, "expiry_ms")
    elif isinstance(payload, SetBrightnessPayload):
        if not 0 <= payload.brightness_percent <= 100:
            raise PayloadError("brightness_percent must be 0..100")
        _validate_u16(payload.current_limit_ma, "current_limit_ma")
    elif isinstance(payload, ActionResultPayload):
        _validate_u16(payload.detail, "detail")
    elif isinstance(payload, KeyEventPayload):
        _validate_u8(payload.key_id, "key_id")
        _validate_u16(payload.duration_ms, "duration_ms")
        _validate_u8(payload.modifiers, "modifiers")
    elif isinstance(payload, EncoderDeltaPayload):
        if not -32768 <= payload.delta <= 32767:
            raise PayloadError("delta must fit int16")
        _validate_u8(payload.acceleration, "acceleration")
    elif isinstance(
        payload,
        (EncoderClickPayload, JoystickEventPayload, TouchEventPayload),
    ):
        _validate_u16(payload.duration_ms, "duration_ms")
    elif isinstance(payload, DeviceStatusPayload):
        _validate_u8(payload.firmware_major, "firmware_major")
        _validate_u8(payload.firmware_minor, "firmware_minor")
        _validate_u32(payload.fault_flags, "fault_flags")
    elif isinstance(payload, BatteryLevelPayload):
        _validate_u16(payload.millivolts, "millivolts")
        if not 0 <= payload.percent <= 100:
            raise PayloadError("battery percent must be 0..100")
        _validate_u8(payload.flags, "flags")
    elif isinstance(payload, ActionIntentPayload):
        _validate_u32(payload.epoch, "epoch")
        _validate_u32(payload.session_id, "session_id")
        _validate_u32(payload.state_version, "state_version")
        _validate_u16(payload.hold_ms, "hold_ms")


def encode_payload(message_type: MessageType, payload: Payload) -> bytes:
    """Encode and validate one message payload."""

    _validate_payload(message_type, payload)
    if message_type is MessageType.STATE_SNAPSHOT:
        assert isinstance(payload, StateSnapshotPayload)
        header = struct.pack(
            "<III4B",
            payload.epoch,
            payload.selected_session_id,
            payload.state_version,
            payload.brightness_percent,
            int(payload.mode),
            int(payload.battery_display_mode),
            len(payload.leds),
        )
        encoded = header + bytes(channel for color in payload.leds for channel in color)
    else:
        spec = _FIXED_SPECS[message_type]
        encoded = struct.pack(
            spec.format,
            *(int(getattr(payload, field.name)) for field in fields(payload)),
        )
    if len(encoded) > MAX_PAYLOAD:
        raise PayloadError("encoded payload exceeds protocol v1 limit")
    return encoded


def decode_payload(message_type: MessageType, raw: bytes) -> Payload:
    """Decode one payload and reject unknown enum values."""

    if message_type is MessageType.STATE_SNAPSHOT:
        if len(raw) < 16:
            raise PayloadError("STATE_SNAPSHOT payload is shorter than 16 bytes")
        (
            epoch,
            selected_session_id,
            state_version,
            brightness,
            mode_raw,
            battery_mode_raw,
            led_count,
        ) = struct.unpack("<III4B", raw[:16])
        expected_length = 16 + led_count * 3
        if led_count > 12 or len(raw) != expected_length:
            raise PayloadError("STATE_SNAPSHOT LED count does not match payload")
        try:
            mode = ModeCode(mode_raw)
            battery_mode = BatteryDisplayMode(battery_mode_raw)
        except ValueError as error:
            raise PayloadError(f"unknown STATE_SNAPSHOT enum: {error}") from error
        leds = tuple(
            (raw[offset], raw[offset + 1], raw[offset + 2])
            for offset in range(16, len(raw), 3)
        )
        payload: Payload = StateSnapshotPayload(
            epoch,
            selected_session_id,
            state_version,
            brightness,
            mode,
            battery_mode,
            leds,
        )
    else:
        spec = _FIXED_SPECS.get(message_type)
        if spec is None:
            raise PayloadError(f"no payload schema for {message_type.name}")
        expected_length = struct.calcsize(spec.format)
        if len(raw) != expected_length:
            raise PayloadError(
                f"{message_type.name} payload must be {expected_length} bytes"
            )
        values = list(struct.unpack(spec.format, raw))
        names = [field.name for field in fields(spec.payload_type)]
        for index, name in enumerate(names):
            enum_type = spec.enum_fields.get(name)
            if enum_type is not None:
                try:
                    values[index] = enum_type(values[index])
                except ValueError as error:
                    raise PayloadError(
                        f"unknown {message_type.name}.{name}: {values[index]}"
                    ) from error
        payload = spec.payload_type(*values)
    _validate_payload(message_type, payload)
    return payload


@dataclass(frozen=True)
class Envelope:
    message_type: MessageType
    sequence: int
    request_id: int = 0
    flags: EnvelopeFlag = EnvelopeFlag.NONE
    payload: bytes = b""
    major: int = PROTOCOL_MAJOR

    _HEADER: ClassVar[struct.Struct] = struct.Struct("<BBBBHH")

    @classmethod
    def from_payload(
        cls,
        message_type: MessageType,
        sequence: int,
        payload: Payload,
        *,
        request_id: int = 0,
        flags: EnvelopeFlag = EnvelopeFlag.NONE,
    ) -> "Envelope":
        return cls(
            message_type=message_type,
            sequence=sequence,
            request_id=request_id,
            flags=flags,
            payload=encode_payload(message_type, payload),
        )

    def decoded_payload(self) -> Payload:
        return decode_payload(self.message_type, self.payload)

    def encode(self, *, hid_report: bool = False) -> bytes:
        if self.major != PROTOCOL_MAJOR:
            raise EnvelopeError(f"unsupported protocol major {self.major}")
        _validate_u16(self.sequence, "sequence")
        _validate_u16(self.request_id, "request_id")
        if int(self.flags) & ~int(KNOWN_FLAGS):
            raise EnvelopeError("reserved flag bits are set")
        if len(self.payload) > MAX_PAYLOAD:
            raise EnvelopeError("payload exceeds 56-byte limit")
        wire = self._HEADER.pack(
            self.major,
            int(self.message_type),
            int(self.flags),
            len(self.payload),
            self.sequence,
            self.request_id,
        ) + self.payload
        if hid_report:
            wire += bytes(HID_REPORT_SIZE - len(wire))
        return wire

    @classmethod
    def decode(cls, raw: bytes) -> "Envelope":
        if len(raw) < HEADER_SIZE:
            raise EnvelopeError("envelope is shorter than 8-byte header")
        major, type_raw, flags_raw, length, sequence, request_id = cls._HEADER.unpack(
            raw[:HEADER_SIZE]
        )
        if major != PROTOCOL_MAJOR:
            raise EnvelopeError(f"unsupported protocol major {major}")
        try:
            message_type = MessageType(type_raw)
        except ValueError as error:
            raise EnvelopeError(f"unknown message type 0x{type_raw:02x}") from error
        if flags_raw & ~int(KNOWN_FLAGS):
            raise EnvelopeError("reserved flag bits are set")
        if length > MAX_PAYLOAD:
            raise EnvelopeError("payload length exceeds 56-byte limit")
        exact_length = HEADER_SIZE + length
        if len(raw) == HID_REPORT_SIZE and exact_length < HID_REPORT_SIZE:
            if any(raw[exact_length:]):
                raise EnvelopeError("USB HID report has non-zero padding")
        elif len(raw) != exact_length:
            raise EnvelopeError(
                f"envelope length mismatch: header says {exact_length}, got {len(raw)}"
            )
        return cls(
            message_type=message_type,
            sequence=sequence,
            request_id=request_id,
            flags=EnvelopeFlag(flags_raw),
            payload=bytes(raw[HEADER_SIZE:exact_length]),
            major=major,
        )


class SequenceTracker:
    """Reject duplicates and backward/stale sequence numbers per epoch."""

    def __init__(self) -> None:
        self._epoch: int | None = None
        self._last: int | None = None

    def reset(self, epoch: int) -> None:
        _validate_u32(epoch, "epoch")
        self._epoch = epoch
        self._last = None

    def accept(self, epoch: int, sequence: int) -> None:
        _validate_u32(epoch, "epoch")
        _validate_u16(sequence, "sequence")
        if self._epoch != epoch:
            self.reset(epoch)
        if self._last is None:
            self._last = sequence
            return
        difference = (sequence - self._last) & 0xFFFF
        if difference == 0:
            raise SequenceError("duplicate sequence")
        if difference >= 0x8000:
            raise SequenceError("stale sequence")
        self._last = sequence


def payload_to_dict(payload: Payload) -> dict[str, Any]:
    """Convert payload dataclasses to JSON-safe primitive values."""

    result: dict[str, Any] = {}
    for field in fields(payload):
        value = getattr(payload, field.name)
        if isinstance(value, IntEnum):
            result[field.name] = value.name.lower()
        elif isinstance(value, tuple):
            result[field.name] = [list(item) if isinstance(item, tuple) else item for item in value]
        else:
            result[field.name] = value
    return result
