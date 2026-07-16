# Official source register

Accessed: 2026-07-16

These links are the evidence baseline for board-level claims. Before schematic release, record the revision printed on each purchased board and download the matching official schematic locally for review. Links may move; do not substitute reseller pinout images for the official sources.

## Seeed Studio XIAO ESP32-S3 Plus

- [Official XIAO ESP32-S3 Series wiki](https://wiki.seeedstudio.com/xiao_esp32s3_getting_started/) — Plus D0–D19 map, power pins, strapping caution, boot/reset, battery behavior, and official design resource links.
- [Official XIAO ESP32-S3 Plus schematic PDF](https://files.seeedstudio.com/wiki/SeeedStudio-XIAO-ESP32S3/res/XIAO_ESP32S3_Plus_SCH_PDF.pdf) — board nets, battery/charger, bottom pads, USB, and XIAO headers. Search result identified V1.1 dated 2025-07-24; confirm against the exact downloaded file at design freeze.
- [Official XIAO Plus baseboard KiCad project](https://files.seeedstudio.com/wiki/SeeedStudio-XIAO-ESP32S3/res/XIAO_Plus_Base_with_botton_pad_lead_out_V1.0.zip) — source for the physical Plus land pattern transcribed into the adapter draft. Pad geometry still requires a purchased-board fit check.
- [Espressif ESP32-S3 datasheet](https://documentation.espressif.com/esp32-s3_datasheet_en.pdf) — silicon pin restrictions, ADC channels, USB D+/D-, and strapping pins.
- [Espressif ESP32-S3 hardware design guidelines](https://documentation.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32s3/schematic-checklist.html) — boot straps, USB layout, reset and GPIO guidance.
- [ESP-IDF USB Device Stack](https://docs.espressif.com/projects/esp-idf/en/stable/esp32s3/api-reference/peripherals/usb_device.html) — HID, vendor, composite device, endpoint, and native USB constraints.

## Seeed Studio XIAO nRF52840 Plus

- [Official XIAO nRF52840 Series wiki](https://wiki.seeedstudio.com/XIAO_BLE/) — Plus D0–D19 map, interfaces, battery read notes, charger, SWD, and official design resource links.
- [Official XIAO nRF52840 Plus schematic PDF](https://files.seeedstudio.com/wiki/XIAO-BLE/Seeed_Studio_XIAO_nRF52840_Plus_PDF.pdf) — board nets, charger, bottom pads, USB, and XIAO headers. Confirm board and schematic revision before release.
- [Nordic nRF52840 Product Specification](https://docs.nordicsemi.com/r/bundle/ps_nrf52840/) — electrical limits, GPIO, USB, radio, SAADC, power, and NFC.
- [Nordic nRF52840 pin assignments](https://docs.nordicsemi.com/r/bundle/ps_nrf52840/page/pin.html) — authoritative AIN-capable pin names and digital pin restrictions.

## Known documentation cautions

- The Seeed ESP32-S3 Plus wiki labels D11/GPIO38 as ADC, while the Espressif GPIO reference does not list GPIO38 as an ADC channel. V1 treats D11 as digital only.
- The Seeed nRF52840 Plus wiki labels several D11–D15 rows as ADC even though Nordic identifies analog inputs by specific `AIN` pin names. V1 only treats D0–D5 and D16 as analog-capable where the Nordic pin assignment supports it.
- D16 is a battery measurement path on both boards, but the surrounding circuitry and enable behavior are not equivalent.
- A current wiki page may describe a newer board revision than purchased hardware. The silkscreen and exact schematic revision are part of test evidence.

## Component sources to add before schematic freeze

Sources already used by the engineering draft:

- [Microchip MCP23017 data sheet](https://ww1.microchip.com/downloads/aemDocuments/documents/APID/ProductDocuments/DataSheets/MCP23017-Data-Sheet-DS20001952.pdf) — SOIC-28 pin allocation, address/reset, I2C, and interrupt pins.
- [Microchip AT42QT1010 data sheet](https://ww1.microchip.com/downloads/en/DeviceDoc/40001946A.pdf) — SOT-23-6 pinout and the `SNSK`/`SNS`/`Cs` single-electrode reference circuit.
- [TI SN74AHCT1G125 data sheet](https://www.ti.com/lit/gpn/sn74ahct1g125) — AHCT input threshold, active-low output enable, and DBV pinout.
- [TI TPS2552/TPS2553 data sheet](https://www.ti.com/lit/ds/slvs841e/slvs841e.pdf) — DBV pinout, active-high TPS2553 enable, fault output, and `ILIM` equation. The draft uses 232 kΩ as a candidate near 117 mA typical; tolerance and optical tests remain required.
- [Panasonic 10TPF150ML official model page](https://industrial.panasonic.com/ww/products/pt/poscap/models/10TPF150ML) — provisional low-profile RGB bulk capacitor candidate. Panasonic lists 150 uF, 10 V, D3L size, and a 7.3 mm × 4.3 mm × 2.8 mm body; exact land pattern and polarity require drawing review before fabrication.
- [Kailh CPG151101S11-16 official drawing and specification](https://m.kailhswitch.com/uploads/15927/files/CPG151101S11-16.pdf?rnd=10) — MX hot-swap socket profile, bottom-side assembly, recommended PCB layout, 1.85 mm body height, 3 mm switch-pin holes, and 5,000-cycle candidate life. Verify the purchased revision against the drawing.
- [ALPS Alpine RKJXM1015004 official product page](https://tech.alpsalpine.com/e/products/detail/RKJXM1015004/) — 8-direction stick switch with center push, 11 mm × 11 mm × 6.6 mm body, official mounting drawing, output table, and CAD download. The V1 firmware uses cardinal contacts and treats diagonals as simultaneous contacts.
- [Work Louder Creator Micro 2 official product page](https://worklouder.cc/creator-micro-2) — public exterior/function reference for a low round joystick-cap construction. It does not establish the unpublished Codex Micro internal component, circuit, or key count.

## Public Codex Micro experience references

These sources support only observable exterior/function decisions. They are not evidence for the unpublished MCU, circuit, dimensions, firmware, or protocol.

- [The Verge: OpenAI made a $230 keyboard to control Codex](https://www.theverge.com/ai-artificial-intelligence/965901/openai-hardware-codex-micro-launch) — public product imagery shows a wide microphone-labelled key immediately right of the circular touch control; reporting describes push-to-talk as a configurable command-key action.
- [Axios: OpenAI launches a keypad for AI agents](https://www.axios.com/2026/07/15/openai-keyboard-codex-agents) — independently reports customizable keys including a push-to-talk option.

Add official manufacturer data sheets for the selected:

- RGB LED and level shifter
- current-limited load switch
- exact MX mechanical switch and keycap
- encoder
- adapter connector
- ESD/protection parts
- Li-Po cell and connector
