#pragma once

#include <array>
#include <cstddef>
#include <cstdint>

namespace agent_deck {

struct Rgb {
  std::uint8_t red{0};
  std::uint8_t green{0};
  std::uint8_t blue{0};
};

struct RgbPowerPolicy {
  std::uint16_t current_budget_ma{250};
  std::uint8_t channel_full_scale_ma{20};
  std::uint8_t led_idle_ma{1};
  std::uint8_t brightness{255};
};

struct RgbFrame {
  static constexpr std::size_t kMaximumLeds = 12;

  std::array<Rgb, kMaximumLeds> pixels{};
  std::uint8_t scale{0};
  std::uint16_t estimated_current_ma{0};
  bool power_limited{false};
  bool power_enabled{false};
};

RgbFrame scale_rgb_frame(const Rgb* requested,
                         std::size_t led_count,
                         const RgbPowerPolicy& policy);

}  // namespace agent_deck
