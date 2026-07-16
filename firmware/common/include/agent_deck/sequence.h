#pragma once

#include <cstdint>

namespace agent_deck {

enum class SequenceDecision : std::uint8_t {
  accepted_first,
  accepted,
  accepted_new_epoch,
  duplicate,
  stale,
};

class PeerSequenceTracker {
 public:
  SequenceDecision observe(std::uint32_t epoch, std::uint16_t sequence);
  void reset();

  bool initialized() const { return initialized_; }
  std::uint32_t epoch() const { return epoch_; }
  std::uint16_t last_sequence() const { return last_sequence_; }

 private:
  bool initialized_{false};
  std::uint32_t epoch_{0};
  std::uint16_t last_sequence_{0};
};

class LocalSequencer {
 public:
  void begin_epoch(std::uint32_t epoch, std::uint16_t first_sequence = 0);
  std::uint16_t next();

  std::uint32_t epoch() const { return epoch_; }

 private:
  std::uint32_t epoch_{0};
  std::uint16_t next_sequence_{0};
};

}  // namespace agent_deck
