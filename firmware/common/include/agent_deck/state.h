#pragma once

#include <cstdint>

namespace agent_deck {

enum class AgentState : std::uint8_t {
  idle = 0,
  running = 1,
  waiting_approval = 2,
  waiting_input = 3,
  completed = 4,
  failed = 5,
  disconnected = 6,
};

class HeartbeatMonitor {
 public:
  explicit HeartbeatMonitor(std::uint32_t timeout_ms = 5000)
      : timeout_ms_(timeout_ms) {}

  void mark_alive(std::uint32_t now_ms);
  bool poll_expired(std::uint32_t now_ms);
  void reset();

  bool alive() const { return alive_; }
  std::uint32_t timeout_ms() const { return timeout_ms_; }

 private:
  std::uint32_t timeout_ms_;
  std::uint32_t last_alive_ms_{0};
  bool alive_{false};
};

struct StateExpiry {
  bool expired{false};
  AgentState previous_state{AgentState::disconnected};
};

class AgentStateCache {
 public:
  explicit AgentStateCache(std::uint32_t heartbeat_timeout_ms = 5000)
      : heartbeat_(heartbeat_timeout_ms) {}

  void apply_snapshot(std::uint32_t bridge_epoch,
                      std::uint32_t session_id,
                      std::uint32_t state_version,
                      AgentState state,
                      std::uint32_t now_ms);

  bool heartbeat(std::uint32_t bridge_epoch, std::uint32_t now_ms);
  StateExpiry poll(std::uint32_t now_ms);
  void disconnect();

  AgentState state() const { return state_; }
  std::uint32_t bridge_epoch() const { return bridge_epoch_; }
  std::uint32_t session_id() const { return session_id_; }
  std::uint32_t state_version() const { return state_version_; }
  bool alive() const { return heartbeat_.alive(); }

 private:
  HeartbeatMonitor heartbeat_;
  AgentState state_{AgentState::disconnected};
  std::uint32_t bridge_epoch_{0};
  std::uint32_t session_id_{0};
  std::uint32_t state_version_{0};
  bool epoch_initialized_{false};
};

}  // namespace agent_deck
