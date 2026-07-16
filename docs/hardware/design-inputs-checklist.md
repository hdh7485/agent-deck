# Schematic-freeze input checklist

Do not start the release schematic until every blocking item has an owner, value, source, and review state. Items marked `measure` require a physical sample or coupon.

## Product and control map

- [ ] Name and physical location of all 12 keys.
- [x] Reserve K11 beside the touch control as the default hold-to-talk key; remapping remains a bridge policy.
- [ ] Optical behavior and state priority for all 12 RGB keys.
- [ ] Default encoder rotation/click actions and modifier behavior.
- [ ] Navigation direction/center actions and simultaneous-contact policy.
- [ ] Touch tap, double-tap, and long-press timing targets.
- [ ] Which actions are sensitive and their confirmation gestures.
- [ ] Host OS support order and minimum Codex/Hermes/OMX/tmux versions or capability assumptions.

## Mechanical switches and keycaps

- [x] MX family selected for the V1 fit-check; Choc overlap explicitly excluded.
- [x] V1 switch fit-check candidate selected as CHERRY `MX2A-L1NB`, the 5-pin PCB-mount RGB Red variant.
- [x] Hot-swap socket candidate locked to Kailh `CPG151101S11-16` with official drawing.
- [ ] Promote the switch from fit-check candidate to order lock after the exact purchased suffix, revision, official drawing, plate retention, LED opening, and socket fit are checked.
- [ ] Key pitch, row/column geometry, rotation, and plate cutout locked.
- [ ] Keycap profile, height, translucent regions, and collision envelope.
- [ ] Plate thickness and PCB-to-plate spacing verified from the selected switch/socket stack.
- [x] Gateron `KS-52B200T-01` screw-in stabilizer selected as the 2u K11 fit-check candidate; the official STEP yields a 23.8 mm stabilizer-center spacing.
- [ ] Import the stabilizer STEP on the PCB datum, derive the exact holes and service envelope, and verify the selected 2u keycap and physical sample before order lock.
- [ ] Per-key diode package, direction, and assembly access.

## Encoder

- [x] ALPS Alpine `EC11E15244G1` selected as the fit-check encoder: vertical, 30 detents/15 pulses, push-on, nominal 20 mm long Ø6 mm flat shaft, and official mounting drawing.
- [ ] Confirm board-to-top height, knob engagement, mounting-tab fit, and purchased-part suffix with an encoder sample before order lock.
- [ ] Knob diameter/height and finger clearance.
- [ ] Encoder body height relative to PCB, plate, and enclosure.
- [ ] Maximum actuation torque/force transferred to plate or enclosure support.
- [ ] Debounce network values selected after scope measurement.

## Navigation switch

- [x] ALPS Alpine `RKJXM1015004` selected as the navigation fit-check candidate; the official body is 11 mm × 11 mm × 6.6 mm and the function is 8-direction plus center push.
- [ ] Transcribe and independently check every official terminal/support hole, then verify the footprint and cap attachment with a physical sample; 8-direction motion is interpreted as cardinal contacts plus simultaneous-contact diagonals.
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
- [x] Retain Panasonic `10TPF150ML` only as the verified 7.3 mm × 4.3 mm × 2.8 mm D3L geometry reference; its official status is NRFND and it is excluded from order lock.
- [ ] Revalidate `10TAE150ML` lifecycle, land pattern, ESR, inrush, and stock as a same-envelope replacement. `10TVE150ML` has the same envelope but its current North American series page is marked discontinued.
- [ ] Battery-only RGB requirement: off, reduced, or full; if non-off, boost/power-mux design approved.

## Common PCB and adapter connector

- [x] Low-profile adapter fit-check pair selected as Samtec `HLE-110-02-G-DV-A` plus `TSM-110-04-L-DV-A`, 2 × 10 contacts on 2.54 mm pitch.
- [x] Use 7.47 mm as the nominal HLE/TSM fit-check PCB stack height; Samtec's official characterization report covers the same `HLE -02` and `TSM -04` lead styles.
- [ ] Confirm the exact 10-position `-A` CAD models, series prints, tolerance stack, current rating, insertion cycles, retention, assembly side, and measured mated height before order lock.
- [ ] Connector pinout includes multiple ground contacts and no unsafe hot-plug assumption.
- [ ] Semantic net direction, voltage, reset level, and owner documented for every pin.
- [ ] Adapter identity method selected.
- [ ] Service access for XIAO reset/boot/SWD/UART defined.
- [ ] XIAO USB-C cable envelope and enclosure opening measured.
- [ ] Both RF antenna keep-outs modeled with the actual battery and plate material.

## Power and battery

- [ ] Exact purchased XIAO revisions and matching official schematics captured in test evidence.
- [x] Jauch `LP603443JU` selected as the protected-cell fit-check candidate: 3.7 V, 850 mAh, catalog cell envelope 6.0 mm × 34.5 mm × 45.0 mm.
- [ ] Obtain the configured pack delivery drawing and sample to lock protection-PCB protrusion, lead exit, connector, wire length, polarity, swelling allowance, and maximum charge/discharge ratings.
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
- [x] Official sources captured for the named V1 mechanical and low-profile fit-check candidates.
- [ ] Exact formal delivery drawings, purchased samples, measured envelopes, and lifecycle evidence attached for every part promoted to order lock.
- [ ] BOM alternatives reviewed for pin/footprint/firmware compatibility; none assumed drop-in without evidence.
- [ ] ERC/DRC pass and waivers reviewed.
- [ ] 3D stack interference review complete.
- [ ] First-article bring-up checklist prepared from `.omx/plans/test-spec-agent-deck-v1.md`.
