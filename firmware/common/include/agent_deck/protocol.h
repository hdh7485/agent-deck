#pragma once

#include <array>
#include <cstddef>
#include <cstdint>

namespace agent_deck::protocol {

constexpr std::uint8_t kProtocolMajor = 1;
constexpr std::size_t kHeaderSize = 8;
constexpr std::size_t kMaximumPayloadSize = 56;
constexpr std::size_t kUsbReportSize = 64;
constexpr std::uint8_t kKnownFlagMask = 0x07;

enum class MessageType : std::uint8_t {
  hello = 0x01,
  hello_ack = 0x02,
  heartbeat = 0x03,
  ack = 0x04,
  state_snapshot = 0x10,
  set_agent_state = 0x11,
  set_selected_agent = 0x12,
  set_led = 0x13,
  set_brightness = 0x14,
  set_mode = 0x15,
  action_result = 0x16,
  set_battery_display_mode = 0x17,
  key_event = 0x20,
  encoder_delta = 0x21,
  encoder_click = 0x22,
  joystick_event = 0x23,
  touch_event = 0x24,
  device_status = 0x25,
  battery_level = 0x26,
  action_intent = 0x27,
};

enum class Flag : std::uint8_t {
  ack_required = 0x01,
  response = 0x02,
  error = 0x04,
};

enum class FrameMode : std::uint8_t {
  compact,
  usb_hid_report,
};

enum class CodecError : std::uint8_t {
  none,
  null_buffer,
  packet_too_short,
  size_mismatch,
  unsupported_major,
  unknown_message_type,
  invalid_flags,
  payload_too_large,
  output_too_small,
  nonzero_padding,
};

struct Envelope {
  MessageType type{MessageType::heartbeat};
  std::uint8_t flags{0};
  std::uint8_t length{0};
  std::uint16_t sequence{0};
  std::uint16_t request_id{0};
  std::array<std::uint8_t, kMaximumPayloadSize> payload{};
};

struct EncodeResult {
  CodecError error{CodecError::none};
  std::size_t size{0};
};

struct DecodeResult {
  CodecError error{CodecError::none};
  Envelope envelope{};
};

constexpr bool is_known_message_type(std::uint8_t value) {
  switch (static_cast<MessageType>(value)) {
    case MessageType::hello:
    case MessageType::hello_ack:
    case MessageType::heartbeat:
    case MessageType::ack:
    case MessageType::state_snapshot:
    case MessageType::set_agent_state:
    case MessageType::set_selected_agent:
    case MessageType::set_led:
    case MessageType::set_brightness:
    case MessageType::set_mode:
    case MessageType::action_result:
    case MessageType::set_battery_display_mode:
    case MessageType::key_event:
    case MessageType::encoder_delta:
    case MessageType::encoder_click:
    case MessageType::joystick_event:
    case MessageType::touch_event:
    case MessageType::device_status:
    case MessageType::battery_level:
    case MessageType::action_intent:
      return true;
  }
  return false;
}

EncodeResult encode(const Envelope& envelope,
                    std::uint8_t* output,
                    std::size_t output_capacity,
                    FrameMode mode);

DecodeResult decode(const std::uint8_t* input,
                    std::size_t input_size,
                    FrameMode mode);

}  // namespace agent_deck::protocol
