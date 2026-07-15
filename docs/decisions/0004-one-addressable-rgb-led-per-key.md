# ADR-0004: Fit one addressable RGB LED to every mechanical key

Status: accepted for V1 engineering draft  
Date: 2026-07-16

## Decision

Increase the common input PCB from six to thirteen SK6812 Mini-E-compatible LEDs so every mechanical key has independent status lighting. Keep the existing one-wire `RGB_DATA` chain, default-off `RGB_PWR_EN`, 5 V level shifter, current-limited load switch, local 100 nF capacitor per LED, and provisional 120 mA aggregate firmware budget.

## Drivers

- Per-key lighting can show session selection, input layers, pending actions, and safety confirmation without adding a display.
- Addressable LEDs add no MCU GPIO as the chain grows; both MCU adapters keep the same semantic connector.
- Fitting the optional positions now avoids a later PCB spin solely for lighting.

## Constraints

- Thirteen requested full-white pixels cannot be assumed safe or useful at unrestricted brightness.
- Firmware must apply a frame-wide brightness/current clamp; the TPS2553 remains the hardware backstop rather than the normal regulator of animation brightness.
- Added switching current and data routing must not compromise the adjacent capacitive-touch electrode.
- Exact LED land pattern, reverse-mount cutout, keycap optical stack, and current-limit resistor remain fabrication blockers.

## Rejected alternatives

- Six illuminated keys only: limits semantic feedback and makes the unlit keys mechanically inconsistent.
- Discrete non-addressable RGB LEDs: would require a dedicated matrix/driver and more routing without a V1 benefit.
- Raise the hardware limit immediately: rejected until optical brightness, USB budget, transient, and thermal measurements exist.

## Consequences

- The common PCB carries LED1 through LED13 and thirteen local decoupling capacitors.
- Protocol capabilities and firmware mapping expose 13 physical LED indices.
- Power tests include an all-LED requested-white case and verify the aggregate software clamp.
- GPIO allocation and both MCU adapter boards remain unchanged.
