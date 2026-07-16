#pragma once

#include <cstdint>

namespace agent_deck {

enum class SemanticAction : std::uint8_t {
  approve = 1,
  reject = 2,
  interrupt = 3,
  push = 4,
  deploy = 5,
  delete_action = 6,
  new_task = 7,
  run_tests = 8,
  open_diff = 9,
  change_reasoning = 10,
  push_to_talk = 11,
};

enum class ConfirmationGesture : std::uint8_t {
  short_press = 1,
  long_press = 2,
  double_press = 3,
  chord = 4,
};

enum class SafetyClass : std::uint8_t {
  ordinary,
  guarded,
  destructive,
};

enum class SafetyDisposition : std::uint8_t {
  ordinary_event,
  semantic_intent,
  reject_ambiguous,
};

struct SafetyPolicy {
  std::uint32_t guarded_long_press_ms{600};
  std::uint32_t destructive_long_press_ms{1200};
};

struct SafetyClassification {
  SafetyClass safety_class{SafetyClass::ordinary};
  SafetyDisposition disposition{SafetyDisposition::ordinary_event};
};

SafetyClass safety_class_for(SemanticAction action);

SafetyClassification classify_safety_gesture(
    SemanticAction action,
    ConfirmationGesture gesture,
    std::uint32_t hold_ms,
    const SafetyPolicy& policy = {});

}  // namespace agent_deck
