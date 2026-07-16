#include "agent_deck/safety.h"

namespace agent_deck {
namespace {

bool known_action(SemanticAction action) {
  const auto value = static_cast<std::uint8_t>(action);
  return value >= static_cast<std::uint8_t>(SemanticAction::approve) &&
         value <= static_cast<std::uint8_t>(SemanticAction::push_to_talk);
}

}  // namespace

SafetyClass safety_class_for(SemanticAction action) {
  switch (action) {
    case SemanticAction::approve:
    case SemanticAction::reject:
    case SemanticAction::interrupt:
      return SafetyClass::guarded;
    case SemanticAction::push:
    case SemanticAction::deploy:
    case SemanticAction::delete_action:
      return SafetyClass::destructive;
    case SemanticAction::new_task:
    case SemanticAction::run_tests:
    case SemanticAction::open_diff:
    case SemanticAction::change_reasoning:
    case SemanticAction::push_to_talk:
      return SafetyClass::ordinary;
  }
  return SafetyClass::destructive;
}

SafetyClassification classify_safety_gesture(
    SemanticAction action,
    ConfirmationGesture gesture,
    std::uint32_t hold_ms,
    const SafetyPolicy& policy) {
  if (!known_action(action)) {
    return {SafetyClass::destructive,
            SafetyDisposition::reject_ambiguous};
  }
  const SafetyClass safety_class = safety_class_for(action);
  if (safety_class == SafetyClass::ordinary) {
    return {safety_class, SafetyDisposition::ordinary_event};
  }

  if (safety_class == SafetyClass::guarded) {
    const bool confirmed =
        gesture == ConfirmationGesture::double_press ||
        gesture == ConfirmationGesture::chord ||
        (gesture == ConfirmationGesture::long_press &&
         hold_ms >= policy.guarded_long_press_ms);
    return {safety_class,
            confirmed ? SafetyDisposition::semantic_intent
                      : SafetyDisposition::reject_ambiguous};
  }

  const bool confirmed =
      gesture == ConfirmationGesture::double_press ||
      gesture == ConfirmationGesture::chord ||
      (gesture == ConfirmationGesture::long_press &&
       hold_ms >= policy.destructive_long_press_ms);
  return {safety_class,
          confirmed ? SafetyDisposition::semantic_intent
                    : SafetyDisposition::reject_ambiguous};
}

}  // namespace agent_deck
