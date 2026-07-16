#include "agent_deck/rgb.h"

#include <algorithm>
#include <cstdint>

namespace agent_deck {
namespace {

std::uint32_t color_current_x255(const Rgb* pixels,
                                 std::size_t led_count,
                                 std::uint8_t channel_full_scale_ma) {
  std::uint32_t total = 0;
  for (std::size_t index = 0; index < led_count; ++index) {
    const std::uint32_t channel_sum =
        static_cast<std::uint32_t>(pixels[index].red) +
        static_cast<std::uint32_t>(pixels[index].green) +
        static_cast<std::uint32_t>(pixels[index].blue);
    total += channel_sum * channel_full_scale_ma;
  }
  return total;
}

std::uint8_t scale_channel(std::uint8_t value, std::uint8_t scale) {
  return static_cast<std::uint8_t>(
      (static_cast<std::uint16_t>(value) * scale) / 255U);
}

}  // namespace

RgbFrame scale_rgb_frame(const Rgb* requested,
                         std::size_t led_count,
                         const RgbPowerPolicy& policy) {
  RgbFrame result{};
  if (requested == nullptr || led_count == 0U) {
    return result;
  }
  led_count = std::min(led_count, RgbFrame::kMaximumLeds);

  for (std::size_t index = 0; index < led_count; ++index) {
    result.pixels[index] = {
        scale_channel(requested[index].red, policy.brightness),
        scale_channel(requested[index].green, policy.brightness),
        scale_channel(requested[index].blue, policy.brightness),
    };
  }

  const std::uint32_t idle_current_ma =
      static_cast<std::uint32_t>(led_count) * policy.led_idle_ma;
  if (policy.current_budget_ma <= idle_current_ma) {
    result.pixels.fill({});
    result.scale = 0;
    result.estimated_current_ma = 0;
    result.power_limited = true;
    result.power_enabled = false;
    return result;
  }
  result.power_enabled = true;

  const std::uint32_t requested_color_x255 =
      color_current_x255(result.pixels.data(), led_count,
                         policy.channel_full_scale_ma);
  const std::uint32_t available_color_x255 =
      static_cast<std::uint32_t>(policy.current_budget_ma - idle_current_ma) *
      255U;

  std::uint8_t current_scale = 255;
  if (requested_color_x255 > available_color_x255 &&
      requested_color_x255 != 0U) {
    const std::uint64_t numerator =
        static_cast<std::uint64_t>(available_color_x255) * 255U;
    current_scale = static_cast<std::uint8_t>(
        std::min<std::uint64_t>(255U, numerator / requested_color_x255));
    for (std::size_t index = 0; index < led_count; ++index) {
      result.pixels[index] = {
          scale_channel(result.pixels[index].red, current_scale),
          scale_channel(result.pixels[index].green, current_scale),
          scale_channel(result.pixels[index].blue, current_scale),
      };
    }
    result.power_limited = true;
  }
  result.scale = static_cast<std::uint8_t>(
      (static_cast<std::uint16_t>(policy.brightness) * current_scale) / 255U);

  const std::uint32_t output_color_x255 =
      color_current_x255(result.pixels.data(), led_count,
                         policy.channel_full_scale_ma);
  const std::uint32_t estimated =
      idle_current_ma + ((output_color_x255 + 254U) / 255U);
  result.estimated_current_ma = static_cast<std::uint16_t>(
      std::min<std::uint32_t>(estimated, 0xFFFFU));
  return result;
}

}  // namespace agent_deck
