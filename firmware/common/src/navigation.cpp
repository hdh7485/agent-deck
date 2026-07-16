#include "agent_deck/navigation.h"

namespace agent_deck {
namespace {

constexpr std::uint8_t kNavigationMask = 0x1FU;

bool has_multiple_bits(std::uint8_t value) {
  return value != 0U &&
         (value & static_cast<std::uint8_t>(value - 1U)) != 0U;
}

std::uint8_t first_priority_bit(std::uint8_t value) {
  constexpr std::uint8_t priority[] = {
      static_cast<std::uint8_t>(1U
                                << static_cast<std::uint8_t>(
                                       NavigationContact::center)),
      static_cast<std::uint8_t>(
          1U << static_cast<std::uint8_t>(NavigationContact::up)),
      static_cast<std::uint8_t>(
          1U << static_cast<std::uint8_t>(NavigationContact::right)),
      static_cast<std::uint8_t>(
          1U << static_cast<std::uint8_t>(NavigationContact::down)),
      static_cast<std::uint8_t>(
          1U << static_cast<std::uint8_t>(NavigationContact::left)),
  };
  for (const std::uint8_t bit : priority) {
    if ((value & bit) != 0U) {
      return bit;
    }
  }
  return 0;
}

}  // namespace

NavigationDebouncer::NavigationDebouncer(
    std::uint32_t debounce_ms,
    NavigationSimultaneousPolicy policy)
    : debouncer_(5, debounce_ms), policy_(policy) {}

std::size_t NavigationDebouncer::update(std::uint8_t raw_contacts,
                                        std::uint32_t now_ms,
                                        SwitchEvent* events,
                                        std::size_t event_capacity) {
  return debouncer_.update(normalize(raw_contacts), now_ms, events,
                           event_capacity);
}

std::size_t NavigationDebouncer::force_release(
    std::uint32_t now_ms,
    SwitchEvent* events,
    std::size_t event_capacity) {
  return debouncer_.force_release(now_ms, events, event_capacity);
}

std::uint8_t NavigationDebouncer::stable_contacts() const {
  return static_cast<std::uint8_t>(debouncer_.stable_mask());
}

std::uint8_t NavigationDebouncer::normalize(
    std::uint8_t raw_contacts) const {
  raw_contacts = static_cast<std::uint8_t>(raw_contacts & kNavigationMask);
  if (!has_multiple_bits(raw_contacts)) {
    return raw_contacts;
  }
  if (policy_ == NavigationSimultaneousPolicy::reject_all) {
    return 0;
  }
  return first_priority_bit(raw_contacts);
}

}  // namespace agent_deck
