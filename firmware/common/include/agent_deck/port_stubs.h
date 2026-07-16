#pragma once

#include "agent_deck/platform_port.h"

namespace agent_deck::ports {

PlatformPort make_esp_idf_bench_stub();
PlatformPort make_zephyr_bench_stub();

}  // namespace agent_deck::ports
