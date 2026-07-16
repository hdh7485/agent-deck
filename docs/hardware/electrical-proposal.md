# V1 electrical proposal

This is a design baseline, not a released schematic. Exact footprints, ratings, thresholds, and power cases require manufacturer-data-sheet review and bench verification.

## Block diagram

```mermaid
flowchart TB
    X[XIAO MCU adapter] -->|3V3, I2C, INT, encoder, RGB control| C[Common input PCB]
    USB[Onboard USB-C] --> X
    BAT[Protected 1-cell Li-Po] --> X

    subgraph C[Common input PCB]
        M[12 keys + 12 diodes\n4x4 matrix] --> IOX[MCP23017 @ 3.3V]
        NAV[5-way digital nav] --> IOX
        PAD[Circular copper electrode] --> TOUCH[AT42QT1010-class touch IC] --> IOX
        ENC[EC11 A/B/click] --> ECOND[RC/ESD optional conditioning] --> X
        IOX -->|INT| X
        X -->|RGB_DATA| LSH[74AHCT1G125]
        VBUS[VBUS_5V] --> LIM[Current-limited load switch]
        X -->|RGB_PWR_EN| LIM
        LIM --> LED[12 addressable RGB LEDs]
        LSH -->|330R series| LED
    end
```

## Key matrix

- Arrange 12 switches in a 4-row × 4-column logical matrix; leave four locations unpopulated.
- Add one 1N4148W-class diode per key with a single documented current direction.
- Put all eight row/column lines on MCP23017 port A: `GPA0..3 = ROW0..3`, `GPA4..7 = COL0..3`.
- Scan one driven row at a time and read columns. Exact active polarity is fixed by the diode orientation and recorded in the schematic notes.
- V1 uses centered 5-pin MX-compatible switch holes and one bottom-mounted Kailh `CPG151101S11-16` socket per key. It does not use a universal MX/Choc overlap.
- Keep the reverse-mount RGB package south of each stem and the socket body north. K11 uses the same electrical footprint at a 29 mm touch-to-key center pitch, but carries a 2u keycap and defaults to host-side push-to-talk.
- The 2u K11 does not consume another matrix input or RGB channel: it remains one MX switch, one diode, and one addressable LED. Press and release are both reported so the bridge can bound host microphone capture.
- The exact switch MPN, keycaps, and K11 stabilizer remain open, but the V1 fit-check plate is now 14.2 mm MX at 1.5 mm nominal thickness. Add stabilizer geometry from the selected manufacturer drawing, then verify socket land pattern, PCB thickness, plate latching, insertion force, and touch clearance with physical samples before fabrication.

## MCP23017 allocation

| MCP23017 pin | Net | Use |
| --- | --- | --- |
| GPA0–GPA3 | `ROW0`–`ROW3` | Key matrix drive |
| GPA4–GPA7 | `COL0`–`COL3` | Key matrix sense |
| GPB0 | `NAV_UP_N` | Navigation input |
| GPB1 | `NAV_DOWN_N` | Navigation input |
| GPB2 | `NAV_LEFT_N` | Navigation input |
| GPB3 | `NAV_RIGHT_N` | Navigation input |
| GPB4 | `NAV_CENTER_N` | Navigation input |
| GPB5 | `TOUCH_OUT` | Touch controller digital output |
| GPB6–GPB7 | `SPARE_IOX0/1` | Test pads, uncommitted |
| INTB | `IOX_INT` | Navigation/touch interrupt to MCU |
| INTA | DNP/test pad | Optional matrix/diagnostic interrupt |

Use 3.3 V supply, local 100 nF decoupling, address straps with explicit resistors, I2C pull-ups sized after bus capacitance is known, and a connector-visible reset/test strategy. V1 keeps the expander because it makes the common adapter interface small and deterministic. V2 may remove it if measured latency, sleep current, cost, or availability outweighs the layout benefit.

## Navigation switch choice

### Direct digital inputs through MCP23017 — recommended

Advantages:

- No ADC-reference or threshold differences between MCUs.
- Simple per-direction diagnostics and deterministic center event.
- Clear handling of simultaneous contacts.
- No extra MCU pins because the expander already exists.

Costs:

- Five expander pins and a larger switch footprint.
- I2C sampling/interrupt latency, which must be measured.

### Resistor ladder to one ADC

Advantages:

- One MCU analog input and fewer connector signals if no expander is used.

Costs:

- Thresholds vary with resistor tolerance, ADC gain/reference, supply, noise, and board calibration.
- Simultaneous directions may create ambiguous voltages.
- ESP and Nordic ADC behavior requires separate calibration.
- D16 cannot be reused because it is reserved for battery sensing.

Decision: use five digital contacts on MCP23017 for V1. Keep a resistor-ladder test coupon only if future cost or pin pressure justifies it.

The current mechanical candidate is ALPS Alpine `RKJXM1015004`, an official 11 mm × 11 mm × 6.6 mm through-hole stick switch with center push. It can expose cardinal directions as separate digital contacts while diagonal motion becomes simultaneous cardinal contacts. The PCB still labels its land pattern as provisional until every official terminal and support hole is transcribed and checked. A separate 14 mm low round concave cap provides the desired exterior feel; it does not imply that the public reference product uses the same internal switch.

## Encoder

- Use an EC11-class encoder with metal mounting tabs and a locked shaft height.
- Connect A, B, and click directly to `ENC_A`, `ENC_B`, and `ENC_SW` on the adapter.
- Provide optional DNP RC footprints so edge shaping can be tuned after scope measurements.
- Use Schmitt-capable GPIO input configuration where available and decode quadrature with a transition table, not independent edge counters.
- The plate or enclosure must support actuation torque; solder pads are not the only mechanical restraint.

## Touch

- Use one round copper electrode with a keep-out from noisy RGB and USB traces.
- Use an AT42QT1010-class one-channel controller to keep MCU behavior common.
- Connect its digital output to MCP23017 GPB5.
- Implement tap, long press, and double tap from timestamps in the common firmware layer.
- Do not claim swipe recognition from one electrode. Swipe requires a later multi-electrode and controller redesign.
- Add a tuning/test coupon for electrode diameter, overlay thickness, ground hatch, and sensitivity component before freezing the enclosure.

## RGB and power

- Twelve SK6812 Mini-E-compatible addressable RGB LEDs, one per key, are the optical baseline; verify exact package and footprint before release layout.
- Feed data through a 74AHCT1G125-class 3.3 V-to-5 V buffer. Keep output enable in a defined state.
- In the V1 draft, power the buffer from `VBUS_5V` and use an MMBT3904-class inverter so the active-low output enable follows `RGB_PWR_EN`: reset/default-low disables both the TPS2553 and the data driver.
- Place approximately 330 ohm in series with the first LED data input and route the chain away from the touch electrode.
- Place 100 nF at each LED, one 10 uF X7R local capacitor on the LED rail, and a low-profile board-entry bulk capacitor; final values follow transient and DC-bias measurements.
- Replace the tall 470 uF radial draft part with Panasonic `10TPF150ML` as the provisional low-profile bulk candidate: 150 uF, 10 V, and 7.3 mm × 4.3 mm × 2.8 mm according to Panasonic's official model table. The KiCad draft uses a conservative EIA-7343-31 land pattern; the exact Panasonic recommended land pattern and polarity marking remain fabrication blockers.
- Feed the LED rail through a current-limited load switch with default-off enable. Candidate families include TPS2553 or AP22653; exact current-set value is selected after LED current measurements.
- The current KiCad draft uses TPS2553DBVR with a 232 kOhm 1% `ILIM` candidate, approximately 117 mA typical from TI's equation. This is a starting point, not a guaranteed maximum; tolerance and transient testing decide the release value.
- Calculate traces and connectors for the selected LED's data-sheet worst case, but enforce a lower aggregate firmware budget. The provisional product budget remains 120 mA total across all 12 LEDs, 10 mA average per LED when all are active, until optical and transient testing justify another value.
- Increasing the chain from six to twelve LEDs consumes no additional MCU GPIO: `RGB_DATA` and `RGB_PWR_EN` remain the only MCU-side RGB signals. Firmware must scale or clamp a complete frame before transmission rather than relying only on the load switch.
- On USB power, `VBUS_5V` supplies the LED switch. In initial battery-only testing, RGB may remain disabled. Full battery-mode RGB requires a separately reviewed boost/power-mux design and is not silently powered from an undefined XIAO 5 V pin.

## Power partition

- The common PCB consumes 3.3 V for MCP23017, touch, and logic.
- Add one 10 uF X7R local bulk capacitor on the 3.3 V rail in addition to device-level 100 nF decoupling; verify effective capacitance at the actual DC bias.
- Each adapter owns its XIAO battery pads, charge behavior, reset/boot, and USB placement.
- The common PCB must not add a second Li-Po charger while the XIAO charger is in circuit.
- Use a protected cell and keyed connector after polarity is locked.
- Provide current measurement points for total device, RGB rail, and 3.3 V logic.
- First power-up always uses a current-limited bench supply with the XIAO removed, then with one adapter installed.

## Protection and layout provisions

- Add ESD protection where external metal or connector exposure warrants it; exact parts depend on connector topology.
- Add series/DNP footprints on long or edge-sensitive signals that are difficult to rework after PCB assembly.
- Respect both XIAO RF antenna keep-outs and keep copper, battery, plate metal, and fast LED edges away from the antenna region.
- Keep touch sense routing short, guarded as the touch IC recommends, and separated from USB/RGB/power-switch nodes.
- Give encoder and navigation mounting tabs mechanical copper and keep-out treatment according to their data sheets.
