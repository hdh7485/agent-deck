#pragma once

#include <array>
#include <cstddef>
#include <cstdint>

#include "agent_deck/safety.h"

namespace agent_deck::protocol {

struct HeartbeatPayload {
  static constexpr std::size_t kEncodedSize = 4;
  std::uint32_t uptime_ms{0};
};

struct ActionIntentPayload {
  static constexpr std::size_t kEncodedSize = 16;

  std::uint32_t bridge_epoch{0};
  std::uint32_t session_id{0};
  std::uint32_t state_version{0};
  SemanticAction action{SemanticAction::approve};
  ConfirmationGesture gesture{ConfirmationGesture::short_press};
  std::uint16_t hold_ms{0};
};

std::array<std::uint8_t, HeartbeatPayload::kEncodedSize> encode_heartbeat(
    const HeartbeatPayload& payload);

bool decode_heartbeat(const std::uint8_t* data,
                      std::size_t size,
                      HeartbeatPayload& payload);

std::array<std::uint8_t, ActionIntentPayload::kEncodedSize>
encode_action_intent(const ActionIntentPayload& payload);

bool decode_action_intent(const std::uint8_t* data,
                          std::size_t size,
                          ActionIntentPayload& payload);

}  // namespace agent_deck::protocol
