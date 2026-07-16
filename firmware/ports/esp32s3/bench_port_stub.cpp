#include "agent_deck/port_stubs.h"

namespace agent_deck::ports {
namespace {

std::uint32_t monotonic_ms(void*) {
  return 0;
}

bool read_input_expander(void*, std::uint16_t*) {
  return false;
}

bool read_encoder(void*, bool*, bool*, bool*) {
  return false;
}

bool set_rgb_power(void*, bool) {
  return false;
}

bool write_rgb(void*, const Rgb*, std::size_t) {
  return false;
}

bool send_control_frame(void*, const std::uint8_t*, std::size_t) {
  return false;
}

}  // namespace

PlatformPort make_esp_idf_bench_stub() {
  return {
      nullptr,
      monotonic_ms,
      read_input_expander,
      read_encoder,
      set_rgb_power,
      write_rgb,
      send_control_frame,
  };
}

}  // namespace agent_deck::ports
