#include "agent_deck/touch.h"

namespace agent_deck {

TouchGestureRecognizer::TouchGestureRecognizer(TouchTiming timing)
    : debouncer_(1, timing.debounce_ms), timing_(timing) {}

void TouchGestureRecognizer::append_event(TouchEventType type,
                                          std::uint32_t duration_ms,
                                          TouchEvent* events,
                                          std::size_t event_capacity,
                                          std::size_t& event_count) {
  if (events != nullptr && event_count < event_capacity) {
    events[event_count] = {type, duration_ms};
    ++event_count;
  }
}

std::size_t TouchGestureRecognizer::update(bool raw_touched,
                                           std::uint32_t now_ms,
                                           TouchEvent* events,
                                           std::size_t event_capacity) {
  std::size_t event_count = 0;
  if (pending_tap_ &&
      static_cast<std::uint32_t>(now_ms - pending_tap_release_ms_) >
          timing_.double_tap_gap_ms) {
    append_event(TouchEventType::tap, pending_tap_duration_ms_, events,
                 event_capacity, event_count);
    pending_tap_ = false;
  }

  SwitchEvent switch_event{};
  const std::size_t switch_event_count =
      debouncer_.update(raw_touched ? 1U : 0U, now_ms, &switch_event, 1);

  if (switch_event_count != 0U) {
    if (switch_event.pressed) {
      press_started_ms_ = now_ms;
      long_emitted_ = false;
      append_event(TouchEventType::raw_press, 0, events, event_capacity,
                   event_count);
    } else {
      const std::uint32_t duration_ms =
          static_cast<std::uint32_t>(now_ms - press_started_ms_);
      if (!long_emitted_ && duration_ms >= timing_.long_press_ms) {
        append_event(TouchEventType::long_press, duration_ms, events,
                     event_capacity, event_count);
        long_emitted_ = true;
      }
      append_event(TouchEventType::raw_release, duration_ms, events,
                   event_capacity, event_count);

      if (!long_emitted_ && duration_ms <= timing_.tap_max_ms) {
        if (pending_tap_ &&
            static_cast<std::uint32_t>(now_ms - pending_tap_release_ms_) <=
                timing_.double_tap_gap_ms) {
          append_event(TouchEventType::double_tap, duration_ms, events,
                       event_capacity, event_count);
          pending_tap_ = false;
        } else {
          pending_tap_ = true;
          pending_tap_release_ms_ = now_ms;
          pending_tap_duration_ms_ = duration_ms;
        }
      }
    }
  }

  if (pressed() && !long_emitted_ &&
      static_cast<std::uint32_t>(now_ms - press_started_ms_) >=
          timing_.long_press_ms) {
    append_event(
        TouchEventType::long_press,
        static_cast<std::uint32_t>(now_ms - press_started_ms_), events,
        event_capacity, event_count);
    long_emitted_ = true;
  }

  return event_count;
}

void TouchGestureRecognizer::reset() {
  debouncer_.reset();
  long_emitted_ = false;
  pending_tap_ = false;
  press_started_ms_ = 0;
  pending_tap_release_ms_ = 0;
  pending_tap_duration_ms_ = 0;
}

}  // namespace agent_deck
