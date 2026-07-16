# Schematic-freeze input checklist

Do not start the release schematic until every blocking item has an owner, value, source, and review state. Items marked `measure` require a physical sample or coupon.

## Product and control map

- [ ] Name and physical location of all 13 keys.
- [ ] Optical behavior and state priority for all 13 RGB keys.
- [ ] Default encoder rotation/click actions and modifier behavior.
- [ ] Navigation direction/center actions and simultaneous-contact policy.
- [ ] Touch tap, double-tap, and long-press timing targets.
- [ ] Which actions are sensitive and their confirmation gestures.
- [ ] Host OS support order and minimum Codex/Hermes/OMX/tmux versions or capability assumptions.

## Mechanical switches and keycaps

- [x] MX family selected for the V1 fit-check; Choc overlap explicitly excluded.
- [x] Hot-swap socket candidate locked to Kailh `CPG151101S11-16` with official drawing.
- [ ] Exact MX switch MPN and manufacturer drawing selected.
- [ ] Key pitch, row/column geometry, rotation, and plate cutout locked.
- [ ] Keycap profile, height, translucent regions, and collision envelope.
- [ ] Plate thickness and PCB-to-plate spacing verified from the selected switch/socket stack.
- [ ] Stabilizers or larger keys explicitly included or ruled out.
- [ ] Per-key diode package, direction, and assembly access.

## Encoder

- [ ] Exact MPN, detent/pulse count, shaft type/diameter/length, bushing, and mounting tabs.
- [ ] Knob diameter/height and finger clearance.
- [ ] Encoder body height relative to PCB, plate, and enclosure.
- [ ] Maximum actuation torque/force transferred to plate or enclosure support.
- [ ] Debounce network values selected after scope measurement.

## Navigation switch

- [ ] Validate the ALPS Alpine `RKJXM1015004` candidate and transcribe every official terminal/support hole; its 8-direction motion is interpreted as four cardinal contacts plus simultaneous-contact diagonals.
- [ ] Center/direction actuation force, travel, cap dimensions, and mounting tab geometry.
- [x] V1 exterior cap envelope set to a provisional 14 mm low round concave profile.
- [ ] Plate/enclosure support strategy.
- [ ] Firmware rule for opposing or diagonal simultaneous contacts.

## Touch

- [ ] Touch controller exact MPN/package and official reference circuit.
- [ ] Electrode diameter and copper layer.
- [ ] Overlay material, dielectric constant if available, and thickness.
- [ ] Ground keep-out/hatch, guard routing, and adjacent LED/USB clearance.
- [ ] Sensitivity component range and tuning footprint.
- [ ] `measure`: coupon performance with dry finger, humid finger, grounded enclosure contact, USB activity, RGB switching, and charging.
- [ ] Swipe explicitly excluded unless a multi-electrode redesign is approved.

## RGB and optics

- [ ] Exact LED MPN, voltage/current limits, package drawing, pinout, reflow limits, and data timing.
- [ ] Translucent keycap or light-pipe geometry and LED-to-key alignment.
- [ ] Maximum useful brightness measured in the actual key stack.
- [ ] Firmware total-current budget and per-state brightness table.
- [ ] Level shifter and current-limited load-switch MPNs and equations.
- [ ] Per-LED and bulk capacitor values/voltage ratings.
- [ ] Battery-only RGB requirement: off, reduced, or full; if non-off, boost/power-mux design approved.

## Common PCB and adapter connector

- [ ] Adapter connector family, exact mating pair, pin count, pitch, stack height, insertion cycles, current rating, and retention.
- [ ] Connector pinout includes multiple ground contacts and no unsafe hot-plug assumption.
- [ ] Semantic net direction, voltage, reset level, and owner documented for every pin.
- [ ] Adapter identity method selected.
- [ ] Service access for XIAO reset/boot/SWD/UART defined.
- [ ] XIAO USB-C cable envelope and enclosure opening measured.
- [ ] Both RF antenna keep-outs modeled with the actual battery and plate material.

## Power and battery

- [ ] Exact purchased XIAO revisions and matching official schematics captured in test evidence.
- [ ] Protected one-cell Li-Po capacity, dimensions, connector, wire exit, and maximum charge/discharge ratings.
- [ ] Battery connector polarity permanently documented; never trust wire color alone.
- [ ] Each XIAO onboard charger behavior, current, thermal case, and power-path limitation verified.
- [ ] No charger duplication or USB/battery back-feed path.
- [ ] 3.3 V common-load budget and XIAO regulator margin calculated.
- [ ] USB worst-case and declared current budget calculated.
- [ ] Battery voltage measurement divider/enable sequence verified for both boards.
- [ ] Test points for ground, VBUS, 3V3, battery, and RGB rail included.
- [ ] Power switch or shipping-mode requirement decided.

## PCB fabrication and assembly

- [ ] Board thickness, copper weight, finish, minimum rules, via rules, and panel constraints.
- [ ] Hot-swap/socket and connector assembly side locked.
- [ ] All user-load parts have mechanical support beyond fragile pads.
- [ ] Touch electrode manufacturing notes and solder-mask behavior specified.
- [ ] RF and antenna regions have explicit keep-outs on all copper and mechanical layers.
- [ ] Fiducials, tooling, test points, revision labels, and pin-1 marks included.
- [ ] Hand assembly versus SMT assembly split and package-size floor decided.

## Firmware and protocol inputs

- [ ] ESP-IDF and Zephyr/nRF Connect SDK baseline versions selected from supported releases.
- [ ] USB composite descriptor layout and report IDs frozen.
- [ ] BLE services, characteristics, MTU assumptions, bonding, and security policy frozen.
- [ ] Protocol major/minor compatibility and capability bits frozen.
- [ ] Heartbeat/stale-state timeout and reconnection rules frozen.
- [ ] Device update/recovery strategy documented for both boards.

## Release evidence

- [ ] Official source register complete for every selected active part.
- [ ] BOM alternatives reviewed for pin/footprint/firmware compatibility; none assumed drop-in without evidence.
- [ ] ERC/DRC pass and waivers reviewed.
- [ ] 3D stack interference review complete.
- [ ] First-article bring-up checklist prepared from `.omx/plans/test-spec-agent-deck-v1.md`.
