#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <iostream>
#include <limits>

#include "agent_deck/boards/xiao_esp32s3_plus.h"
#include "agent_deck/boards/xiao_nrf52840_plus.h"
#include "agent_deck/debounce.h"
#include "agent_deck/encoder.h"
#include "agent_deck/navigation.h"
#include "agent_deck/port_stubs.h"
#include "agent_deck/protocol.h"
#include "agent_deck/protocol_payloads.h"
#include "agent_deck/rgb.h"
#include "agent_deck/safety.h"
#include "agent_deck/sequence.h"
#include "agent_deck/state.h"
#include "agent_deck/touch.h"
#include "golden_vectors.h"

namespace {

int failures = 0;
int tests_run = 0;

#define CHECK(condition)                                                     \
  do {                                                                       \
    if (!(condition)) {                                                      \
      std::cerr << __FILE__ << ':' << __LINE__ << ": CHECK failed: "        \
                << #condition << '\n';                                       \
      ++failures;                                                            \
    }                                                                        \
  } while (false)

#define CHECK_EQ(left, right) CHECK((left) == (right))

template <typename Function>
void run_test(const char* name, Function function) {
  const int before = failures;
  ++tests_run;
  function();
  std::cout << (failures == before ? "PASS " : "FAIL ") << name << '\n';
}

void test_protocol_heartbeat_golden_vector() {
  using namespace agent_deck::protocol;
  const auto payload = encode_heartbeat({0x01020304U});
  Envelope envelope{};
  envelope.type = MessageType::heartbeat;
  envelope.length = static_cast<std::uint8_t>(payload.size());
  envelope.sequence = 0x1234;
  std::copy(payload.begin(), payload.end(), envelope.payload.begin());

  std::array<std::uint8_t, kUsbReportSize> encoded{};
  const auto encoded_result =
      encode(envelope, encoded.data(), encoded.size(), FrameMode::compact);
  CHECK_EQ(encoded_result.error, CodecError::none);
  CHECK_EQ(encoded_result.size,
           agent_deck::tests::golden::kHeartbeatCompact.size());
  CHECK(std::equal(agent_deck::tests::golden::kHeartbeatCompact.begin(),
                   agent_deck::tests::golden::kHeartbeatCompact.end(),
                   encoded.begin()));

  const auto decoded =
      decode(encoded.data(), encoded_result.size, FrameMode::compact);
  CHECK_EQ(decoded.error, CodecError::none);
  CHECK_EQ(decoded.envelope.type, MessageType::heartbeat);
  CHECK_EQ(decoded.envelope.sequence, 0x1234);
  HeartbeatPayload heartbeat{};
  CHECK(decode_heartbeat(decoded.envelope.payload.data(),
                         decoded.envelope.length, heartbeat));
  CHECK_EQ(heartbeat.uptime_ms, 0x01020304U);
}

void test_protocol_action_intent_golden_vector() {
  using namespace agent_deck;
  using namespace agent_deck::protocol;
  const auto payload = encode_action_intent({
      0x11223344U,
      0x55667788U,
      9U,
      SemanticAction::approve,
      ConfirmationGesture::long_press,
      1000U,
  });
  Envelope envelope{};
  envelope.type = MessageType::action_intent;
  envelope.flags = static_cast<std::uint8_t>(Flag::ack_required);
  envelope.length = static_cast<std::uint8_t>(payload.size());
  envelope.sequence = 0x1235;
  envelope.request_id = 0x2468;
  std::copy(payload.begin(), payload.end(), envelope.payload.begin());

  std::array<std::uint8_t, kUsbReportSize> encoded{};
  const auto encoded_result =
      encode(envelope, encoded.data(), encoded.size(), FrameMode::compact);
  CHECK_EQ(encoded_result.error, CodecError::none);
  CHECK_EQ(encoded_result.size,
           agent_deck::tests::golden::kActionIntentCompact.size());
  CHECK(std::equal(agent_deck::tests::golden::kActionIntentCompact.begin(),
                   agent_deck::tests::golden::kActionIntentCompact.end(),
                   encoded.begin()));

  ActionIntentPayload decoded_payload{};
  CHECK(decode_action_intent(payload.data(), payload.size(), decoded_payload));
  CHECK_EQ(decoded_payload.bridge_epoch, 0x11223344U);
  CHECK_EQ(decoded_payload.session_id, 0x55667788U);
  CHECK_EQ(decoded_payload.state_version, 9U);
  CHECK_EQ(decoded_payload.action, SemanticAction::approve);
  CHECK_EQ(decoded_payload.gesture, ConfirmationGesture::long_press);
  CHECK_EQ(decoded_payload.hold_ms, 1000U);

  auto invalid = payload;
  invalid[12] = 0xFF;
  CHECK(!decode_action_intent(invalid.data(), invalid.size(), decoded_payload));
  invalid = payload;
  invalid[13] = 0;
  CHECK(!decode_action_intent(invalid.data(), invalid.size(), decoded_payload));
}

void test_protocol_usb_and_malformed_frames() {
  using namespace agent_deck::protocol;
  Envelope envelope{};
  envelope.type = MessageType::ack;
  envelope.flags = static_cast<std::uint8_t>(Flag::response);
  envelope.length = 2;
  envelope.payload[0] = 0xAA;
  envelope.payload[1] = 0x55;

  std::array<std::uint8_t, kUsbReportSize> usb{};
  auto result =
      encode(envelope, usb.data(), usb.size(), FrameMode::usb_hid_report);
  CHECK_EQ(result.error, CodecError::none);
  CHECK_EQ(result.size, kUsbReportSize);
  CHECK_EQ(decode(usb.data(), usb.size(), FrameMode::usb_hid_report).error,
           CodecError::none);

  usb[63] = 1;
  CHECK_EQ(decode(usb.data(), usb.size(), FrameMode::usb_hid_report).error,
           CodecError::nonzero_padding);
  usb[63] = 0;
  CHECK_EQ(decode(usb.data(), 63, FrameMode::usb_hid_report).error,
           CodecError::size_mismatch);
  CHECK_EQ(decode(usb.data(), 7, FrameMode::compact).error,
           CodecError::packet_too_short);

  auto malformed = usb;
  malformed[0] = 2;
  CHECK_EQ(decode(malformed.data(), malformed.size(),
                  FrameMode::usb_hid_report)
               .error,
           CodecError::unsupported_major);
  malformed = usb;
  malformed[1] = 0xFF;
  CHECK_EQ(decode(malformed.data(), malformed.size(),
                  FrameMode::usb_hid_report)
               .error,
           CodecError::unknown_message_type);
  malformed = usb;
  malformed[2] = 0x80;
  CHECK_EQ(decode(malformed.data(), malformed.size(),
                  FrameMode::usb_hid_report)
               .error,
           CodecError::invalid_flags);
  malformed = usb;
  malformed[3] = 57;
  CHECK_EQ(decode(malformed.data(), malformed.size(),
                  FrameMode::usb_hid_report)
               .error,
           CodecError::payload_too_large);
  CHECK_EQ(decode(usb.data(), 9, FrameMode::compact).error,
           CodecError::size_mismatch);

  envelope.flags = 0x80;
  CHECK_EQ(encode(envelope, usb.data(), usb.size(), FrameMode::compact).error,
           CodecError::invalid_flags);
  envelope.flags = 0;
  envelope.length = 56;
  CHECK_EQ(encode(envelope, usb.data(), 63, FrameMode::usb_hid_report).error,
           CodecError::output_too_small);
  const auto maximum =
      encode(envelope, usb.data(), usb.size(), FrameMode::compact);
  CHECK_EQ(maximum.error, CodecError::none);
  CHECK_EQ(maximum.size, kUsbReportSize);
  CHECK_EQ(decode(usb.data(), usb.size(), FrameMode::compact).error,
           CodecError::none);
}

void test_sequence_and_epoch_tracking() {
  using namespace agent_deck;
  PeerSequenceTracker tracker;
  CHECK_EQ(tracker.observe(10, 100), SequenceDecision::accepted_first);
  CHECK_EQ(tracker.observe(10, 101), SequenceDecision::accepted);
  CHECK_EQ(tracker.observe(10, 101), SequenceDecision::duplicate);
  CHECK_EQ(tracker.observe(10, 99), SequenceDecision::stale);
  CHECK_EQ(tracker.observe(11, 1), SequenceDecision::accepted_new_epoch);
  CHECK_EQ(tracker.epoch(), 11U);

  tracker.reset();
  CHECK_EQ(tracker.observe(1, 0xFFFE), SequenceDecision::accepted_first);
  CHECK_EQ(tracker.observe(1, 1), SequenceDecision::accepted);

  LocalSequencer local;
  local.begin_epoch(77, 0xFFFF);
  CHECK_EQ(local.next(), 0xFFFF);
  CHECK_EQ(local.next(), 0);
  CHECK_EQ(local.epoch(), 77U);
}

void test_matrix_debounce_and_forced_release() {
  using namespace agent_deck;
  MatrixDebouncer debouncer(12, 5);
  std::array<SwitchEvent, 4> events{};
  CHECK_EQ(debouncer.update(0x001, 0, events.data(), events.size()), 0U);
  CHECK_EQ(debouncer.update(0x000, 2, events.data(), events.size()), 0U);
  CHECK_EQ(debouncer.update(0x001, 3, events.data(), events.size()), 0U);
  CHECK_EQ(debouncer.update(0x001, 7, events.data(), events.size()), 0U);
  CHECK_EQ(debouncer.update(0x001, 8, events.data(), events.size()), 1U);
  CHECK(events[0].pressed);
  CHECK_EQ(events[0].index, 0);
  CHECK_EQ(debouncer.stable_mask(), 0x001);

  CHECK_EQ(debouncer.update(0x000, 20, events.data(), events.size()), 0U);
  CHECK_EQ(debouncer.update(0x000, 25, events.data(), events.size()), 1U);
  CHECK(!events[0].pressed);
  CHECK_EQ(events[0].held_ms, 17U);

  CHECK_EQ(debouncer.update(0x006, 30, events.data(), events.size()), 0U);
  CHECK_EQ(debouncer.update(0x006, 35, events.data(), events.size()), 2U);
  CHECK_EQ(debouncer.force_release(45, events.data(), events.size()), 2U);
  CHECK_EQ(debouncer.stable_mask(), 0);

  const std::uint32_t near_wrap =
      std::numeric_limits<std::uint32_t>::max() - 2U;
  CHECK_EQ(debouncer.update(0x001, near_wrap, events.data(), events.size()),
           0U);
  CHECK_EQ(debouncer.update(0x001, 3, events.data(), events.size()), 1U);
}

void test_navigation_simultaneous_policy() {
  using namespace agent_deck;
  const std::uint8_t up =
      static_cast<std::uint8_t>(1U
                                << static_cast<std::uint8_t>(
                                       NavigationContact::up));
  const std::uint8_t right =
      static_cast<std::uint8_t>(1U
                                << static_cast<std::uint8_t>(
                                       NavigationContact::right));
  const std::uint8_t center =
      static_cast<std::uint8_t>(1U
                                << static_cast<std::uint8_t>(
                                       NavigationContact::center));

  NavigationDebouncer reject(5, NavigationSimultaneousPolicy::reject_all);
  CHECK_EQ(reject.normalize(static_cast<std::uint8_t>(up | right)), 0);
  CHECK_EQ(reject.normalize(up), up);

  NavigationDebouncer priority(
      5, NavigationSimultaneousPolicy::center_then_clockwise_priority);
  CHECK_EQ(priority.normalize(static_cast<std::uint8_t>(up | right)), up);
  CHECK_EQ(priority.normalize(static_cast<std::uint8_t>(up | center)), center);

  std::array<SwitchEvent, 2> events{};
  CHECK_EQ(priority.update(static_cast<std::uint8_t>(up | center), 0,
                           events.data(), events.size()),
           0U);
  CHECK_EQ(priority.update(static_cast<std::uint8_t>(up | center), 5,
                           events.data(), events.size()),
           1U);
  CHECK_EQ(events[0].index,
           static_cast<std::uint8_t>(NavigationContact::center));
}

void test_quadrature_decoder() {
  using namespace agent_deck;
  QuadratureDecoder decoder;
  CHECK_EQ(decoder.update(false, false).detent_delta, 0);
  CHECK_EQ(decoder.update(false, true).detent_delta, 0);
  CHECK_EQ(decoder.update(true, true).detent_delta, 0);
  CHECK_EQ(decoder.update(true, false).detent_delta, 0);
  CHECK_EQ(decoder.update(false, false).detent_delta, 1);

  CHECK_EQ(decoder.update(true, false).detent_delta, 0);
  CHECK_EQ(decoder.update(true, true).detent_delta, 0);
  CHECK_EQ(decoder.update(false, true).detent_delta, 0);
  CHECK_EQ(decoder.update(false, false).detent_delta, -1);

  decoder.reset();
  decoder.update(false, false);
  const auto invalid = decoder.update(true, true);
  CHECK(invalid.invalid_transition);
  CHECK_EQ(invalid.detent_delta, 0);

  QuadratureDecoder inverted(4, true);
  inverted.update(false, false);
  inverted.update(false, true);
  inverted.update(true, true);
  inverted.update(true, false);
  CHECK_EQ(inverted.update(false, false).detent_delta, -1);
}

void test_touch_tap_double_and_long() {
  using namespace agent_deck;
  const TouchTiming timing{5, 100, 200, 300};
  TouchGestureRecognizer touch(timing);
  std::array<TouchEvent, 6> events{};

  CHECK_EQ(touch.update(true, 0, events.data(), events.size()), 0U);
  CHECK_EQ(touch.update(true, 5, events.data(), events.size()), 1U);
  CHECK_EQ(events[0].type, TouchEventType::raw_press);
  CHECK_EQ(touch.update(false, 50, events.data(), events.size()), 0U);
  CHECK_EQ(touch.update(false, 55, events.data(), events.size()), 1U);
  CHECK_EQ(events[0].type, TouchEventType::raw_release);
  CHECK_EQ(touch.update(false, 256, events.data(), events.size()), 1U);
  CHECK_EQ(events[0].type, TouchEventType::tap);
  CHECK_EQ(events[0].duration_ms, 50U);

  touch.reset();
  touch.update(true, 0, events.data(), events.size());
  touch.update(true, 5, events.data(), events.size());
  touch.update(false, 30, events.data(), events.size());
  touch.update(false, 35, events.data(), events.size());
  touch.update(true, 80, events.data(), events.size());
  touch.update(true, 85, events.data(), events.size());
  touch.update(false, 110, events.data(), events.size());
  const auto double_count =
      touch.update(false, 115, events.data(), events.size());
  CHECK_EQ(double_count, 2U);
  CHECK_EQ(events[0].type, TouchEventType::raw_release);
  CHECK_EQ(events[1].type, TouchEventType::double_tap);

  touch.reset();
  touch.update(true, 0, events.data(), events.size());
  touch.update(true, 5, events.data(), events.size());
  touch.update(false, 30, events.data(), events.size());
  touch.update(false, 35, events.data(), events.size());
  touch.update(true, 220, events.data(), events.size());
  touch.update(true, 225, events.data(), events.size());
  CHECK_EQ(touch.update(false, 250, events.data(), events.size()), 1U);
  CHECK_EQ(events[0].type, TouchEventType::tap);
  CHECK_EQ(touch.update(false, 255, events.data(), events.size()), 1U);
  CHECK_EQ(events[0].type, TouchEventType::raw_release);

  touch.reset();
  touch.update(true, 0, events.data(), events.size());
  touch.update(true, 5, events.data(), events.size());
  CHECK_EQ(touch.update(true, 305, events.data(), events.size()), 1U);
  CHECK_EQ(events[0].type, TouchEventType::long_press);
  CHECK_EQ(events[0].duration_ms, 300U);
  touch.update(false, 400, events.data(), events.size());
  CHECK_EQ(touch.update(false, 405, events.data(), events.size()), 1U);
  CHECK_EQ(events[0].type, TouchEventType::raw_release);
}

void test_heartbeat_expiry_and_epoch_change() {
  using namespace agent_deck;
  AgentStateCache cache(100);
  cache.apply_snapshot(7, 99, 4, AgentState::running, 10);
  CHECK(cache.alive());
  CHECK_EQ(cache.state(), AgentState::running);
  CHECK(!cache.poll(110).expired);
  const auto expiry = cache.poll(111);
  CHECK(expiry.expired);
  CHECK_EQ(expiry.previous_state, AgentState::running);
  CHECK_EQ(cache.state(), AgentState::disconnected);
  CHECK_EQ(cache.session_id(), 0U);

  cache.apply_snapshot(7, 101, 5, AgentState::waiting_input, 200);
  CHECK(cache.heartbeat(7, 250));
  CHECK(!cache.heartbeat(8, 260));
  CHECK_EQ(cache.state(), AgentState::disconnected);
  CHECK(cache.alive());
  CHECK_EQ(cache.bridge_epoch(), 8U);
}

void test_rgb_current_budget() {
  using namespace agent_deck;
  std::array<Rgb, RgbFrame::kMaximumLeds> white{};
  white.fill({255, 255, 255});
  const RgbPowerPolicy limited{250, 20, 1, 255};
  const auto frame = scale_rgb_frame(white.data(), white.size(), limited);
  CHECK(frame.power_enabled);
  CHECK(frame.power_limited);
  CHECK(frame.scale < 255);
  CHECK(frame.estimated_current_ma <= limited.current_budget_ma);
  for (const auto& pixel : frame.pixels) {
    CHECK_EQ(pixel.red, pixel.green);
    CHECK_EQ(pixel.green, pixel.blue);
    CHECK(pixel.red < 255);
  }

  const RgbPowerPolicy dim{1000, 20, 1, 128};
  const auto dim_frame = scale_rgb_frame(white.data(), white.size(), dim);
  CHECK(dim_frame.power_enabled);
  CHECK(!dim_frame.power_limited);
  CHECK_EQ(dim_frame.scale, 128);
  CHECK_EQ(dim_frame.pixels[0].red, 128);

  const RgbPowerPolicy off{5, 20, 1, 255};
  const auto off_frame = scale_rgb_frame(white.data(), white.size(), off);
  CHECK(!off_frame.power_enabled);
  CHECK(off_frame.power_limited);
  CHECK_EQ(off_frame.estimated_current_ma, 0);
  CHECK_EQ(off_frame.pixels[0].red, 0);
}

void test_safety_gesture_classification() {
  using namespace agent_deck;
  CHECK_EQ(safety_class_for(SemanticAction::new_task),
           SafetyClass::ordinary);
  CHECK_EQ(classify_safety_gesture(SemanticAction::new_task,
                                   ConfirmationGesture::short_press, 0)
               .disposition,
           SafetyDisposition::ordinary_event);
  CHECK_EQ(classify_safety_gesture(SemanticAction::approve,
                                   ConfirmationGesture::short_press, 0)
               .disposition,
           SafetyDisposition::reject_ambiguous);
  CHECK_EQ(classify_safety_gesture(SemanticAction::approve,
                                   ConfirmationGesture::long_press, 599)
               .disposition,
           SafetyDisposition::reject_ambiguous);
  CHECK_EQ(classify_safety_gesture(SemanticAction::approve,
                                   ConfirmationGesture::long_press, 600)
               .disposition,
           SafetyDisposition::semantic_intent);
  CHECK_EQ(classify_safety_gesture(SemanticAction::delete_action,
                                   ConfirmationGesture::long_press, 1199)
               .disposition,
           SafetyDisposition::reject_ambiguous);
  CHECK_EQ(classify_safety_gesture(SemanticAction::delete_action,
                                   ConfirmationGesture::long_press, 1200)
               .disposition,
           SafetyDisposition::semantic_intent);
  CHECK_EQ(classify_safety_gesture(SemanticAction::deploy,
                                   ConfirmationGesture::double_press, 0)
               .disposition,
           SafetyDisposition::semantic_intent);
  CHECK_EQ(classify_safety_gesture(static_cast<SemanticAction>(0xFF),
                                   ConfirmationGesture::chord, 0)
               .disposition,
           SafetyDisposition::reject_ambiguous);
}

void test_board_definitions_and_port_stubs() {
  using namespace agent_deck;
  CHECK(common_pin_assignment_is_valid(boards::kXiaoEsp32s3Plus));
  CHECK(common_pin_assignment_is_valid(boards::kXiaoNrf52840Plus));
  CHECK_EQ(boards::kXiaoEsp32s3Plus.battery_sense.xiao_d, 16);
  CHECK_EQ(boards::kXiaoNrf52840Plus.battery_sense.xiao_d, 16);
  CHECK_EQ(boards::kXiaoEsp32s3Plus.common_signals[7].signal,
           SemanticSignal::encoder_a);
  CHECK_EQ(boards::kXiaoNrf52840Plus.common_signals[7].xiao_d, 8);

  const auto esp = ports::make_esp_idf_bench_stub();
  const auto nrf = ports::make_zephyr_bench_stub();
  CHECK(esp.valid());
  CHECK(nrf.valid());
  std::uint16_t raw = 0;
  CHECK(!esp.read_input_expander(esp.context, &raw));
  CHECK(!nrf.set_rgb_power(nrf.context, true));
}

}  // namespace

int main() {
  run_test("protocol heartbeat golden vector",
           test_protocol_heartbeat_golden_vector);
  run_test("protocol action-intent golden vector",
           test_protocol_action_intent_golden_vector);
  run_test("protocol malformed and USB frames",
           test_protocol_usb_and_malformed_frames);
  run_test("sequence and epoch tracking", test_sequence_and_epoch_tracking);
  run_test("matrix debounce and forced release",
           test_matrix_debounce_and_forced_release);
  run_test("navigation simultaneous policy",
           test_navigation_simultaneous_policy);
  run_test("quadrature decoder", test_quadrature_decoder);
  run_test("touch gestures", test_touch_tap_double_and_long);
  run_test("heartbeat expiry", test_heartbeat_expiry_and_epoch_change);
  run_test("RGB current budget", test_rgb_current_budget);
  run_test("safety gesture classification",
           test_safety_gesture_classification);
  run_test("board definitions and fail-closed ports",
           test_board_definitions_and_port_stubs);

  if (failures != 0) {
    std::cerr << failures << " assertion(s) failed across " << tests_run
              << " test(s)\n";
    return 1;
  }
  std::cout << "All " << tests_run << " tests passed\n";
  return 0;
}
