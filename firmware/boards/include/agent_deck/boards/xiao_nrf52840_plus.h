#pragma once

#include "agent_deck/board_definition.h"

namespace agent_deck::boards {

inline constexpr BoardDefinition kXiaoNrf52840Plus{
    "Seeed Studio XIAO nRF52840 Plus",
    {{
        {SemanticSignal::rgb_data, 0, 0, 2, pin_digital_output},
        {SemanticSignal::iox_interrupt, 1, 0, 3, pin_digital_input},
        {SemanticSignal::rgb_power_enable, 3, 0, 29, pin_digital_output},
        {SemanticSignal::i2c_sda, 4, 0, 4,
         pin_digital_input | pin_digital_output | pin_open_drain | pin_i2c},
        {SemanticSignal::i2c_scl, 5, 0, 5,
         pin_digital_input | pin_digital_output | pin_open_drain | pin_i2c},
        {SemanticSignal::uart_tx_debug, 6, 1, 11,
         pin_digital_output | pin_uart},
        {SemanticSignal::uart_rx_debug, 7, 1, 12,
         pin_digital_input | pin_uart},
        {SemanticSignal::encoder_a, 8, 1, 13, pin_digital_input},
        {SemanticSignal::encoder_b, 9, 1, 14, pin_digital_input},
        {SemanticSignal::encoder_switch, 10, 1, 15, pin_digital_input},
    }},
    {SemanticSignal::battery_sense, 16, 0, 31,
     pin_digital_input | pin_adc},
};

static_assert(common_pin_assignment_is_valid(kXiaoNrf52840Plus),
              "nRF52840 Plus common pins must be unique and must not use D16");

}  // namespace agent_deck::boards
