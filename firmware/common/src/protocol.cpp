#include "agent_deck/protocol.h"

#include <algorithm>

namespace agent_deck::protocol {
namespace {

void write_u16_le(std::uint8_t* output, std::uint16_t value) {
  output[0] = static_cast<std::uint8_t>(value & 0xFFU);
  output[1] = static_cast<std::uint8_t>((value >> 8U) & 0xFFU);
}

std::uint16_t read_u16_le(const std::uint8_t* input) {
  return static_cast<std::uint16_t>(
      static_cast<std::uint16_t>(input[0]) |
      static_cast<std::uint16_t>(static_cast<std::uint16_t>(input[1]) << 8U));
}

}  // namespace

EncodeResult encode(const Envelope& envelope,
                    std::uint8_t* output,
                    std::size_t output_capacity,
                    FrameMode mode) {
  if (output == nullptr) {
    return {CodecError::null_buffer, 0};
  }
  if (!is_known_message_type(static_cast<std::uint8_t>(envelope.type))) {
    return {CodecError::unknown_message_type, 0};
  }
  if ((envelope.flags & static_cast<std::uint8_t>(~kKnownFlagMask)) != 0U) {
    return {CodecError::invalid_flags, 0};
  }
  if (envelope.length > kMaximumPayloadSize) {
    return {CodecError::payload_too_large, 0};
  }

  const std::size_t compact_size = kHeaderSize + envelope.length;
  const std::size_t encoded_size =
      mode == FrameMode::usb_hid_report ? kUsbReportSize : compact_size;
  if (output_capacity < encoded_size) {
    return {CodecError::output_too_small, 0};
  }

  std::fill(output, output + encoded_size, 0U);
  output[0] = kProtocolMajor;
  output[1] = static_cast<std::uint8_t>(envelope.type);
  output[2] = envelope.flags;
  output[3] = envelope.length;
  write_u16_le(output + 4, envelope.sequence);
  write_u16_le(output + 6, envelope.request_id);
  std::copy_n(envelope.payload.begin(), envelope.length, output + kHeaderSize);

  return {CodecError::none, encoded_size};
}

DecodeResult decode(const std::uint8_t* input,
                    std::size_t input_size,
                    FrameMode mode) {
  DecodeResult result{};
  if (input == nullptr) {
    result.error = CodecError::null_buffer;
    return result;
  }
  if (input_size < kHeaderSize) {
    result.error = CodecError::packet_too_short;
    return result;
  }
  if (mode == FrameMode::usb_hid_report && input_size != kUsbReportSize) {
    result.error = CodecError::size_mismatch;
    return result;
  }
  if (input[0] != kProtocolMajor) {
    result.error = CodecError::unsupported_major;
    return result;
  }
  if (!is_known_message_type(input[1])) {
    result.error = CodecError::unknown_message_type;
    return result;
  }
  if ((input[2] & static_cast<std::uint8_t>(~kKnownFlagMask)) != 0U) {
    result.error = CodecError::invalid_flags;
    return result;
  }

  const std::size_t payload_length = input[3];
  if (payload_length > kMaximumPayloadSize) {
    result.error = CodecError::payload_too_large;
    return result;
  }
  const std::size_t compact_size = kHeaderSize + payload_length;
  if (mode == FrameMode::compact && input_size != compact_size) {
    result.error = CodecError::size_mismatch;
    return result;
  }
  if (input_size < compact_size) {
    result.error = CodecError::packet_too_short;
    return result;
  }
  if (mode == FrameMode::usb_hid_report &&
      std::any_of(input + compact_size, input + input_size,
                  [](std::uint8_t byte) { return byte != 0U; })) {
    result.error = CodecError::nonzero_padding;
    return result;
  }

  result.envelope.type = static_cast<MessageType>(input[1]);
  result.envelope.flags = input[2];
  result.envelope.length = input[3];
  result.envelope.sequence = read_u16_le(input + 4);
  result.envelope.request_id = read_u16_le(input + 6);
  std::copy_n(input + kHeaderSize, payload_length,
              result.envelope.payload.begin());
  result.error = CodecError::none;
  return result;
}

}  // namespace agent_deck::protocol
