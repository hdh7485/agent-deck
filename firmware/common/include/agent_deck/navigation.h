#pragma once

#include <cstddef>
#include <cstdint>

#include "agent_deck/debounce.h"

namespace agent_deck {

enum class NavigationContact : std::uint8_t {
  up = 0,
  right = 1,
  down = 2,
  left = 3,
  center = 4,
};

enum class NavigationSimultaneousPolicy : std::uint8_t {
  reject_all,
  center_then_clockwise_priority,
};

class NavigationDebouncer {
 public:
  explicit NavigationDebouncer(
      std::uint32_t debounce_ms = 8,
      NavigationSimultaneousPolicy policy =
          NavigationSimultaneousPolicy::reject_all);

  std::size_t update(std::uint8_t raw_contacts,
                     std::uint32_t now_ms,
                     SwitchEvent* events,
                     std::size_t event_capacity);

  std::size_t force_release(std::uint32_t now_ms,
                            SwitchEvent* events,
                            std::size_t event_capacity);

  std::uint8_t stable_contacts() const;
  std::uint8_t normalize(std::uint8_t raw_contacts) const;

 private:
  MatrixDebouncer debouncer_;
  NavigationSimultaneousPolicy policy_;
};

}  // namespace agent_deck
