#pragma once

#include <cstddef>
#include <cstdint>

#include "agent_deck/debounce.h"

namespace agent_deck {

enum class TouchEventType : std::uint8_t {
  raw_press,
  raw_release,
  tap,
  double_tap,
  long_press,
};

struct TouchEvent {
  TouchEventType type{TouchEventType::raw_press};
  std::uint32_t duration_ms{0};
};

struct TouchTiming {
  std::uint32_t debounce_ms{20};
  std::uint32_t tap_max_ms{250};
  std::uint32_t double_tap_gap_ms{280};
  std::uint32_t long_press_ms{600};
};

class TouchGestureRecognizer {
 public:
  explicit TouchGestureRecognizer(TouchTiming timing = {});

  std::size_t update(bool raw_touched,
                     std::uint32_t now_ms,
                     TouchEvent* events,
                     std::size_t event_capacity);

  void reset();
  bool pressed() const { return debouncer_.stable_mask() != 0; }

 private:
  static void append_event(TouchEventType type,
                           std::uint32_t duration_ms,
                           TouchEvent* events,
                           std::size_t event_capacity,
                           std::size_t& event_count);

  MatrixDebouncer debouncer_;
  TouchTiming timing_;
  bool long_emitted_{false};
  bool pending_tap_{false};
  std::uint32_t press_started_ms_{0};
  std::uint32_t pending_tap_release_ms_{0};
  std::uint32_t pending_tap_duration_ms_{0};
};

}  // namespace agent_deck
