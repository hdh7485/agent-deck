#include "agent_deck/protocol_payloads.h"

namespace agent_deck::protocol {
namespace {

void write_u16_le(std::uint8_t* output, std::uint16_t value) {
  output[0] = static_cast<std::uint8_t>(value & 0xFFU);
  output[1] = static_cast<std::uint8_t>((value >> 8U) & 0xFFU);
}

void write_u32_le(std::uint8_t* output, std::uint32_t value) {
  output[0] = static_cast<std::uint8_t>(value & 0xFFU);
  output[1] = static_cast<std::uint8_t>((value >> 8U) & 0xFFU);
  output[2] = static_cast<std::uint8_t>((value >> 16U) & 0xFFU);
  output[3] = static_cast<std::uint8_t>((value >> 24U) & 0xFFU);
}

std::uint16_t read_u16_le(const std::uint8_t* input) {
  return static_cast<std::uint16_t>(
      static_cast<std::uint16_t>(input[0]) |
      static_cast<std::uint16_t>(static_cast<std::uint16_t>(input[1]) << 8U));
}

std::uint32_t read_u32_le(const std::uint8_t* input) {
  return static_cast<std::uint32_t>(input[0]) |
         (static_cast<std::uint32_t>(input[1]) << 8U) |
         (static_cast<std::uint32_t>(input[2]) << 16U) |
         (static_cast<std::uint32_t>(input[3]) << 24U);
}

bool valid_action(std::uint8_t value) {
  return value >= static_cast<std::uint8_t>(SemanticAction::approve) &&
         value <= static_cast<std::uint8_t>(SemanticAction::push_to_talk);
}

bool valid_gesture(std::uint8_t value) {
  return value >=
             static_cast<std::uint8_t>(ConfirmationGesture::short_press) &&
         value <= static_cast<std::uint8_t>(ConfirmationGesture::chord);
}

}  // namespace

std::array<std::uint8_t, HeartbeatPayload::kEncodedSize> encode_heartbeat(
    const HeartbeatPayload& payload) {
  std::array<std::uint8_t, HeartbeatPayload::kEncodedSize> output{};
  write_u32_le(output.data(), payload.uptime_ms);
  return output;
}

bool decode_heartbeat(const std::uint8_t* data,
                      std::size_t size,
                      HeartbeatPayload& payload) {
  if (data == nullptr || size != HeartbeatPayload::kEncodedSize) {
    return false;
  }
  payload.uptime_ms = read_u32_le(data);
  return true;
}

std::array<std::uint8_t, ActionIntentPayload::kEncodedSize>
encode_action_intent(const ActionIntentPayload& payload) {
  std::array<std::uint8_t, ActionIntentPayload::kEncodedSize> output{};
  write_u32_le(output.data(), payload.bridge_epoch);
  write_u32_le(output.data() + 4, payload.session_id);
  write_u32_le(output.data() + 8, payload.state_version);
  output[12] = static_cast<std::uint8_t>(payload.action);
  output[13] = static_cast<std::uint8_t>(payload.gesture);
  write_u16_le(output.data() + 14, payload.hold_ms);
  return output;
}

bool decode_action_intent(const std::uint8_t* data,
                          std::size_t size,
                          ActionIntentPayload& payload) {
  if (data == nullptr || size != ActionIntentPayload::kEncodedSize ||
      !valid_action(data[12]) || !valid_gesture(data[13])) {
    return false;
  }
  payload.bridge_epoch = read_u32_le(data);
  payload.session_id = read_u32_le(data + 4);
  payload.state_version = read_u32_le(data + 8);
  payload.action = static_cast<SemanticAction>(data[12]);
  payload.gesture = static_cast<ConfirmationGesture>(data[13]);
  payload.hold_ms = read_u16_le(data + 14);
  return true;
}

}  // namespace agent_deck::protocol
