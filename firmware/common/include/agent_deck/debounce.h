#pragma once

#include <array>
#include <cstddef>
#include <cstdint>

namespace agent_deck {

struct SwitchEvent {
  std::uint8_t index{0};
  bool pressed{false};
  std::uint32_t held_ms{0};
};

class MatrixDebouncer {
 public:
  static constexpr std::size_t kMaximumInputs = 16;

  explicit MatrixDebouncer(std::uint8_t input_count = 16,
                           std::uint32_t debounce_ms = 5);

  std::size_t update(std::uint16_t raw_mask,
                     std::uint32_t now_ms,
                     SwitchEvent* events,
                     std::size_t event_capacity);

  std::size_t force_release(std::uint32_t now_ms,
                            SwitchEvent* events,
                            std::size_t event_capacity);

  void reset();

  std::uint16_t stable_mask() const { return stable_mask_; }
  std::uint8_t input_count() const { return input_count_; }
  std::uint32_t debounce_ms() const { return debounce_ms_; }

 private:
  std::uint8_t input_count_;
  std::uint32_t debounce_ms_;
  std::uint16_t stable_mask_{0};
  std::array<bool, kMaximumInputs> candidate_valid_{};
  std::array<bool, kMaximumInputs> candidate_state_{};
  std::array<std::uint32_t, kMaximumInputs> candidate_since_{};
  std::array<std::uint32_t, kMaximumInputs> pressed_since_{};
};

}  // namespace agent_deck
