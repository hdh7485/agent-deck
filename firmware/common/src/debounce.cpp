#include "agent_deck/debounce.h"

#include <algorithm>

namespace agent_deck {

MatrixDebouncer::MatrixDebouncer(std::uint8_t input_count,
                                 std::uint32_t debounce_ms)
    : input_count_(
          std::min<std::uint8_t>(input_count, kMaximumInputs)),
      debounce_ms_(debounce_ms) {}

std::size_t MatrixDebouncer::update(std::uint16_t raw_mask,
                                    std::uint32_t now_ms,
                                    SwitchEvent* events,
                                    std::size_t event_capacity) {
  std::size_t event_count = 0;
  const std::uint16_t input_mask =
      input_count_ == 16U
          ? 0xFFFFU
          : static_cast<std::uint16_t>((1U << input_count_) - 1U);
  raw_mask = static_cast<std::uint16_t>(raw_mask & input_mask);

  for (std::uint8_t index = 0; index < input_count_; ++index) {
    const std::uint16_t bit = static_cast<std::uint16_t>(1U << index);
    const bool raw = (raw_mask & bit) != 0U;
    const bool stable = (stable_mask_ & bit) != 0U;

    if (raw == stable) {
      candidate_valid_[index] = false;
      continue;
    }
    if (!candidate_valid_[index] || candidate_state_[index] != raw) {
      candidate_valid_[index] = true;
      candidate_state_[index] = raw;
      candidate_since_[index] = now_ms;
      continue;
    }
    if (static_cast<std::uint32_t>(now_ms - candidate_since_[index]) <
        debounce_ms_) {
      continue;
    }

    candidate_valid_[index] = false;
    if (raw) {
      stable_mask_ = static_cast<std::uint16_t>(stable_mask_ | bit);
      pressed_since_[index] = now_ms;
    } else {
      stable_mask_ =
          static_cast<std::uint16_t>(stable_mask_ & static_cast<std::uint16_t>(~bit));
    }

    if (events != nullptr && event_count < event_capacity) {
      events[event_count] = {
          index,
          raw,
          raw ? 0U
              : static_cast<std::uint32_t>(now_ms - pressed_since_[index]),
      };
      ++event_count;
    }
  }
  return event_count;
}

std::size_t MatrixDebouncer::force_release(std::uint32_t now_ms,
                                           SwitchEvent* events,
                                           std::size_t event_capacity) {
  std::size_t event_count = 0;
  for (std::uint8_t index = 0; index < input_count_; ++index) {
    const std::uint16_t bit = static_cast<std::uint16_t>(1U << index);
    candidate_valid_[index] = false;
    if ((stable_mask_ & bit) == 0U) {
      continue;
    }
    if (events != nullptr && event_count < event_capacity) {
      events[event_count] = {
          index,
          false,
          static_cast<std::uint32_t>(now_ms - pressed_since_[index]),
      };
      ++event_count;
    }
  }
  stable_mask_ = 0;
  return event_count;
}

void MatrixDebouncer::reset() {
  stable_mask_ = 0;
  candidate_valid_.fill(false);
  candidate_state_.fill(false);
  candidate_since_.fill(0);
  pressed_since_.fill(0);
}

}  // namespace agent_deck
