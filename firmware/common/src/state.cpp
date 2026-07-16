#include "agent_deck/state.h"

namespace agent_deck {

void HeartbeatMonitor::mark_alive(std::uint32_t now_ms) {
  last_alive_ms_ = now_ms;
  alive_ = true;
}

bool HeartbeatMonitor::poll_expired(std::uint32_t now_ms) {
  if (!alive_ ||
      static_cast<std::uint32_t>(now_ms - last_alive_ms_) <= timeout_ms_) {
    return false;
  }
  alive_ = false;
  return true;
}

void HeartbeatMonitor::reset() {
  last_alive_ms_ = 0;
  alive_ = false;
}

void AgentStateCache::apply_snapshot(std::uint32_t bridge_epoch,
                                     std::uint32_t session_id,
                                     std::uint32_t state_version,
                                     AgentState state,
                                     std::uint32_t now_ms) {
  bridge_epoch_ = bridge_epoch;
  session_id_ = session_id;
  state_version_ = state_version;
  state_ = state;
  epoch_initialized_ = true;
  heartbeat_.mark_alive(now_ms);
}

bool AgentStateCache::heartbeat(std::uint32_t bridge_epoch,
                                std::uint32_t now_ms) {
  if (!epoch_initialized_ || bridge_epoch != bridge_epoch_) {
    disconnect();
    bridge_epoch_ = bridge_epoch;
    epoch_initialized_ = true;
    heartbeat_.mark_alive(now_ms);
    return false;
  }
  heartbeat_.mark_alive(now_ms);
  return true;
}

StateExpiry AgentStateCache::poll(std::uint32_t now_ms) {
  if (!heartbeat_.poll_expired(now_ms)) {
    return {};
  }
  const AgentState previous = state_;
  state_ = AgentState::disconnected;
  session_id_ = 0;
  state_version_ = 0;
  return {true, previous};
}

void AgentStateCache::disconnect() {
  heartbeat_.reset();
  state_ = AgentState::disconnected;
  session_id_ = 0;
  state_version_ = 0;
}

}  // namespace agent_deck
