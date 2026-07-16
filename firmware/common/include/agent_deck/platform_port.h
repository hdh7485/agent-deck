#pragma once

#include <cstddef>
#include <cstdint>

#include "agent_deck/rgb.h"

namespace agent_deck {

struct PlatformPort {
  void* context{nullptr};
  std::uint32_t (*monotonic_ms)(void*){nullptr};
  bool (*read_input_expander)(void*, std::uint16_t*){nullptr};
  bool (*read_encoder)(void*, bool*, bool*, bool*){nullptr};
  bool (*set_rgb_power)(void*, bool){nullptr};
  bool (*write_rgb)(void*, const Rgb*, std::size_t){nullptr};
  bool (*send_control_frame)(void*, const std::uint8_t*, std::size_t){nullptr};

  bool valid() const {
    return monotonic_ms != nullptr && read_input_expander != nullptr &&
           read_encoder != nullptr && set_rgb_power != nullptr &&
           write_rgb != nullptr && send_control_frame != nullptr;
  }
};

}  // namespace agent_deck
