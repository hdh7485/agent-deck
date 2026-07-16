#include "agent_deck/sequence.h"

namespace agent_deck {

SequenceDecision PeerSequenceTracker::observe(std::uint32_t epoch,
                                              std::uint16_t sequence) {
  if (!initialized_) {
    initialized_ = true;
    epoch_ = epoch;
    last_sequence_ = sequence;
    return SequenceDecision::accepted_first;
  }
  if (epoch != epoch_) {
    epoch_ = epoch;
    last_sequence_ = sequence;
    return SequenceDecision::accepted_new_epoch;
  }

  const std::uint16_t forward =
      static_cast<std::uint16_t>(sequence - last_sequence_);
  if (forward == 0U) {
    return SequenceDecision::duplicate;
  }
  if (forward < 0x8000U) {
    last_sequence_ = sequence;
    return SequenceDecision::accepted;
  }
  return SequenceDecision::stale;
}

void PeerSequenceTracker::reset() {
  initialized_ = false;
  epoch_ = 0;
  last_sequence_ = 0;
}

void LocalSequencer::begin_epoch(std::uint32_t epoch,
                                 std::uint16_t first_sequence) {
  epoch_ = epoch;
  next_sequence_ = first_sequence;
}

std::uint16_t LocalSequencer::next() {
  const std::uint16_t current = next_sequence_;
  next_sequence_ = static_cast<std::uint16_t>(next_sequence_ + 1U);
  return current;
}

}  // namespace agent_deck
