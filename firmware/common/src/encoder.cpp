#include "agent_deck/encoder.h"

#include <algorithm>

namespace agent_deck {

QuadratureDecoder::QuadratureDecoder(std::uint8_t transitions_per_detent,
                                     bool invert_direction)
    : transitions_per_detent_(std::clamp<std::uint8_t>(
          transitions_per_detent, 1U, 127U)),
      direction_sign_(invert_direction ? -1 : 1) {}

EncoderUpdate QuadratureDecoder::update(bool channel_a, bool channel_b) {
  static constexpr std::int8_t transition_table[16] = {
      0, 1, -1, 0, -1, 0, 0, 1,
      1, 0, 0, -1, 0, -1, 1, 0,
  };

  const std::uint8_t state =
      static_cast<std::uint8_t>((channel_a ? 2U : 0U) |
                                (channel_b ? 1U : 0U));
  if (!initialized_) {
    initialized_ = true;
    previous_state_ = state;
    return {};
  }

  EncoderUpdate result{};
  if ((previous_state_ ^ state) == 0x03U) {
    result.invalid_transition = true;
    accumulator_ = 0;
    previous_state_ = state;
    return result;
  }

  const std::uint8_t table_index =
      static_cast<std::uint8_t>((previous_state_ << 2U) | state);
  result.transition = static_cast<std::int8_t>(
      transition_table[table_index] * direction_sign_);
  previous_state_ = state;
  accumulator_ =
      static_cast<std::int8_t>(accumulator_ + result.transition);

  if (accumulator_ >= static_cast<std::int8_t>(transitions_per_detent_)) {
    result.detent_delta = 1;
    accumulator_ = 0;
  } else if (accumulator_ <=
             -static_cast<std::int8_t>(transitions_per_detent_)) {
    result.detent_delta = -1;
    accumulator_ = 0;
  }
  return result;
}

void QuadratureDecoder::reset() {
  initialized_ = false;
  previous_state_ = 0;
  accumulator_ = 0;
}

}  // namespace agent_deck
