#pragma once

#include <array>
#include <cstddef>
#include <cstdint>

namespace agent_deck {

enum class SemanticSignal : std::uint8_t {
  rgb_data,
  iox_interrupt,
  rgb_power_enable,
  i2c_sda,
  i2c_scl,
  uart_tx_debug,
  uart_rx_debug,
  encoder_a,
  encoder_b,
  encoder_switch,
  battery_sense,
};

enum PinCapability : std::uint16_t {
  pin_digital_input = 1U << 0U,
  pin_digital_output = 1U << 1U,
  pin_open_drain = 1U << 2U,
  pin_adc = 1U << 3U,
  pin_uart = 1U << 4U,
  pin_i2c = 1U << 5U,
};

struct SemanticPin {
  SemanticSignal signal;
  std::uint8_t xiao_d;
  std::uint8_t port;
  std::uint8_t pin;
  std::uint16_t capabilities;
};

struct BoardDefinition {
  static constexpr std::size_t kCommonSignalCount = 10;

  const char* board_name;
  std::array<SemanticPin, kCommonSignalCount> common_signals;
  SemanticPin battery_sense;
};

constexpr bool common_pin_assignment_is_valid(const BoardDefinition& board) {
  for (std::size_t i = 0; i < board.common_signals.size(); ++i) {
    if (board.common_signals[i].xiao_d == 16U) {
      return false;
    }
    for (std::size_t j = i + 1; j < board.common_signals.size(); ++j) {
      if (board.common_signals[i].xiao_d ==
          board.common_signals[j].xiao_d) {
        return false;
      }
    }
  }
  for (std::uint8_t expected = 0;
       expected < static_cast<std::uint8_t>(SemanticSignal::battery_sense);
       ++expected) {
    std::size_t matches = 0;
    for (const SemanticPin& pin : board.common_signals) {
      if (static_cast<std::uint8_t>(pin.signal) == expected) {
        ++matches;
      }
    }
    if (matches != 1U) {
      return false;
    }
  }
  return board.battery_sense.xiao_d == 16U &&
         board.battery_sense.signal == SemanticSignal::battery_sense;
}

}  // namespace agent_deck
