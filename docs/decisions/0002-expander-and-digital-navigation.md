# ADR-0002: MCP23017 and digital navigation contacts for V1

Status: accepted for V1 planning  
Date: 2026-07-16

## Decision

Use MCP23017 on the common PCB for the 4×4 key matrix, five navigation contacts, and touch-controller output. Keep encoder A/B/click directly connected to the MCU. Do not use an ADC resistor ladder for the V1 navigation switch.

## Drivers

- Reduce the common MCU interface to a small conservative pin subset.
- Avoid cross-MCU ADC thresholds and calibration for navigation input.
- Keep timing-sensitive quadrature edges off I2C.
- Make each navigation direction easy to test and diagnose.

## Alternatives considered

- Directly connect all inputs to MCU GPIO: lower BOM but consumes most candidate pins and couples the main board to MCU-specific details.
- ADC resistor ladder: uses one pin but adds voltage tolerances, simultaneous-press ambiguity, and per-MCU calibration.
- Individual key wiring on MCP23017: simple scanning but leaves insufficient pins for all navigation contacts.

## Consequences

- Firmware needs a shared MCP23017 driver and matrix scanner.
- I2C latency, wake behavior, and sleep current must be measured.
- Two expander pins remain available for fixtures or future low-speed inputs.
- V2 may remove the expander if measurement supports a simpler direct-GPIO design.

