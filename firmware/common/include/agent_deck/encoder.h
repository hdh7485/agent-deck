#pragma once

#include <cstdint>

namespace agent_deck {

struct EncoderUpdate {
  std::int8_t transition{0};
  std::int8_t detent_delta{0};
  bool invalid_transition{false};
};

class QuadratureDecoder {
 public:
  explicit QuadratureDecoder(std::uint8_t transitions_per_detent = 4,
                             bool invert_direction = false);

  EncoderUpdate update(bool channel_a, bool channel_b);
  void reset();

 private:
  bool initialized_{false};
  std::uint8_t previous_state_{0};
  std::int8_t accumulator_{0};
  std::uint8_t transitions_per_detent_;
  std::int8_t direction_sign_;
};

}  // namespace agent_deck
