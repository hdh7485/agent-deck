# Official source register

Accessed: 2026-07-16

These links are the evidence baseline for board-level claims. Before schematic release, record the revision printed on each purchased board and download the matching official schematic locally for review. Links may move; do not substitute reseller pinout images for the official sources.

## Seeed Studio XIAO ESP32-S3 Plus

- [Official XIAO ESP32-S3 Series wiki](https://wiki.seeedstudio.com/xiao_esp32s3_getting_started/) — Plus D0–D19 map, power pins, strapping caution, boot/reset, battery behavior, and official design resource links.
- [Official XIAO ESP32-S3 Plus schematic PDF](https://files.seeedstudio.com/wiki/SeeedStudio-XIAO-ESP32S3/res/XIAO_ESP32S3_Plus_SCH_PDF.pdf) — board nets, battery/charger, bottom pads, USB, and XIAO headers. Search result identified V1.1 dated 2025-07-24; confirm against the exact downloaded file at design freeze.
- [Official XIAO Plus baseboard KiCad project](https://files.seeedstudio.com/wiki/SeeedStudio-XIAO-ESP32S3/res/XIAO_Plus_Base_with_botton_pad_lead_out_V1.0.zip) — source for the physical Plus land pattern transcribed into the adapter draft. Pad geometry still requires a purchased-board fit check.
- [Official XIAO ESP32-S3 Plus KiCad project](https://files.seeedstudio.com/wiki/SeeedStudio-XIAO-ESP32S3/res/XIAO_ESP32S3_Plus_V1.1_KiCad_260115.zip) — source for the 21 mm × 17.8 mm board outline and the nominal USB-C and U.FL component models. Cable, coax, external antenna, and assembled maximum-Z envelopes remain physical checks.
- [Espressif ESP32-S3 datasheet](https://documentation.espressif.com/esp32-s3_datasheet_en.pdf) — silicon pin restrictions, ADC channels, USB D+/D-, and strapping pins.
- [Espressif ESP32-S3 hardware design guidelines](https://documentation.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32s3/schematic-checklist.html) — boot straps, USB layout, reset and GPIO guidance.
- [ESP-IDF USB Device Stack](https://docs.espressif.com/projects/esp-idf/en/stable/esp32s3/api-reference/peripherals/usb_device.html) — HID, vendor, composite device, endpoint, and native USB constraints.

## Seeed Studio XIAO nRF52840 Plus

- [Official XIAO nRF52840 Series wiki](https://wiki.seeedstudio.com/XIAO_BLE/) — Plus D0–D19 map, interfaces, battery read notes, charger, SWD, and official design resource links.
- [Official XIAO nRF52840 Plus schematic PDF](https://files.seeedstudio.com/wiki/XIAO-BLE/Seeed_Studio_XIAO_nRF52840_Plus_PDF.pdf) — board nets, charger, bottom pads, USB, and XIAO headers. Confirm board and schematic revision before release.
- [Official XIAO nRF52840 Plus KiCad project](https://files.seeedstudio.com/wiki/XIAO-BLE/Seeed_Studio_XIAO_nRF52840_Plus.zip) — source for the 21 mm × 17.8 mm board outline and nominal USB, shield, and ceramic-antenna placement. Exact assembled height and RF keep-out remain sample checks.
- [Nordic nRF52840 Product Specification](https://docs.nordicsemi.com/r/bundle/ps_nrf52840/) — electrical limits, GPIO, USB, radio, SAADC, power, and NFC.
- [Nordic nRF52840 pin assignments](https://docs.nordicsemi.com/r/bundle/ps_nrf52840/page/pin.html) — authoritative AIN-capable pin names and digital pin restrictions.

## Known documentation cautions

- The Seeed ESP32-S3 Plus wiki labels D11/GPIO38 as ADC, while the Espressif GPIO reference does not list GPIO38 as an ADC channel. V1 treats D11 as digital only.
- The Seeed nRF52840 Plus wiki labels several D11–D15 rows as ADC even though Nordic identifies analog inputs by specific `AIN` pin names. V1 only treats D0–D5 and D16 as analog-capable where the Nordic pin assignment supports it.
- D16 is a battery measurement path on both boards, but the surrounding circuitry and enable behavior are not equivalent.
- A current wiki page may describe a newer board revision than purchased hardware. The silkscreen and exact schematic revision are part of test evidence.

## Component sources and remaining gaps before schematic freeze

Sources already used by the engineering draft:

- [Microchip MCP23017 data sheet](https://ww1.microchip.com/downloads/aemDocuments/documents/APID/ProductDocuments/DataSheets/MCP23017-Data-Sheet-DS20001952.pdf) — SOIC-28 pin allocation, address/reset, I2C, and interrupt pins.
- [Microchip AT42QT1010 data sheet](https://ww1.microchip.com/downloads/en/DeviceDoc/40001946A.pdf) — SOT-23-6 pinout and the `SNSK`/`SNS`/`Cs` single-electrode reference circuit.
- [TI SN74AHCT1G125 data sheet](https://www.ti.com/lit/gpn/sn74ahct1g125) — AHCT input threshold, active-low output enable, and DBV pinout.
- [TI TPS2552/TPS2553 data sheet](https://www.ti.com/lit/ds/slvs841e/slvs841e.pdf) — DBV pinout, active-high TPS2553 enable, fault output, and `ILIM` equation. The draft uses 232 kΩ as a candidate near 117 mA typical; tolerance and optical tests remain required.
- [Panasonic 10TPF150ML North American model page](https://na.industrial.panasonic.com/products/capacitors/polymer-capacitors/lineup/poscap-tantalum-polymer/series/13072/model/13154) — lists 150 uF, 10 V, D3L, 7.3 mm × 4.3 mm × 2.8 mm, and status `NRFND`. V1 retains the envelope as geometry evidence but excludes this MPN from order lock.
- [Panasonic 10TAE150ML official model page](https://na.industrial.panasonic.com/products/capacitors/polymer-capacitors/lineup/poscap-tantalum-polymer/series/13091/model/13176) — same 150 uF, 10 V, D3L 7.3 mm × 4.3 mm × 2.8 mm envelope with 25 mΩ maximum ESR in the published table. Lifecycle, land pattern, inrush behavior, and regional orderability must be revalidated at BOM freeze.
- [Panasonic TV series official page](https://na.industrial.panasonic.com/products/capacitors/polymer-capacitors/lineup/poscap-tantalum-polymer/series/13115) — lists `10TVE150ML` with the same D3L envelope and 25 mΩ maximum ESR, but marks the TV series discontinued. It is not an order-lock replacement.
- [CHERRY MX2A Red official product page](https://www.cherry.de/en-gb/product/mx2a-red) — identifies `MX2A-L1NB` as the RGB, 5-pin PCB-mount variant and lists 45 cN actuation, 2 mm pretravel, and 4 mm total travel.
- [CHERRY MX2A Red official data sheet](https://www.cherry.de/fileadmin/media/Industrial/Switch/MX_RED/Data_sheet_MX2A_Red.pdf) — distinguishes RGB `MX2A-L1NA/B`, identifies `MX2A-L1NB` as the 5-pin PCB-fixation model, and documents hot-swap suitability and the SMD LED opening.
- [Kailh CPG151101S11-16 official drawing and specification](https://m.kailhswitch.com/uploads/15927/files/CPG151101S11-16.pdf?rnd=10) — MX hot-swap socket profile, bottom-side assembly, recommended PCB layout, 1.85 mm body height, 3 mm switch-pin holes, and 5,000-cycle candidate life. Verify the purchased revision against the drawing.
- [ALPS Alpine EC11E15244G1 official product page](https://tech.alpsalpine.com/e/products/detail/EC11E15244G1/) — identifies the standard vertical encoder, 30 detents/15 pulses, push-on switch, 20 mm actuator length, and manufacturer supply-status classification.
- [ALPS Alpine EC11E series official drawing](https://tech.alpsalpine.com/cms.media/product_catalog_ec_01_ec11e_en_611f078659.pdf) — source for the shaft, body, tab, terminal, and mounting-hole fit-check dimensions.
- [ALPS Alpine RKJXM1015004 official product page](https://tech.alpsalpine.com/e/products/detail/RKJXM1015004/) — 8-direction stick switch with center push, 11 mm × 11 mm × 6.6 mm body, official mounting drawing, output table, and CAD download. The V1 firmware uses cardinal contacts and treats diagonals as simultaneous contacts.
- [ALPS Alpine RKJXM series official drawing](https://tech.alpsalpine.com/cms.media/product_catalog_mu_02_rkjxm_en_afb146521a.pdf) — source for the 15 mm actuator height, shaft geometry, terminal pattern, and mounting-side hole layout; ALPS labels the catalog values as outline specifications, so the delivery specification and sample remain release gates.
- [Gateron screw-in stabilizer official product page](https://www.gateron.com/products/gateron-screw-in-stabilizer) — confirms PCB screw-in construction, normal-travel support, and included 2u wires.
- [Gateron KS-52B200T-01 official STEP archive](https://gateron.com/u_file/2308/01/file/ScrewInStabilizerKS-52B200T-01.rar) — official 3D source used to derive a 23.8 mm 2u stabilizer-center spacing. The model must be imported on the project PCB datum before holes or enclosure clearances are released.
- [Samtec HLE-110-02-G-DV-A official product page](https://www.samtec.com/products/hle-110-02-g-dv-a) — exact 2 × 10, 2.54 mm-pitch low-profile socket fit-check suffix; Samtec requires confirmation against the series print before final design-in.
- [Samtec TSM-110-04-L-DV-A official product page](https://www.samtec.com/products/tsm-110-04-l-dv-a) — exact 2 × 10, 2.54 mm-pitch surface-mount header fit-check suffix.
- [Samtec HLE/TSM 7.47 mm characterization report](https://suddendocs.samtec.com/testreports/hsc-report_tsm-04_hle-02_web.pdf) — explicitly characterizes a 7.47 mm stack using `TSM-130-04-L-DV-A` and `HLE-130-02-G-DV`. V1 applies that value only as a lead-style/series fit-check target; the exact 10-position `-A` pair requires CAD and sample measurement.
- [Jauch lithium-polymer battery official product list](https://www.jauch.com/en-US/products/battery_technology/getPrm/batteries/Lithium%20Polymer%20Batteries/) — lists `LP603443JU` as 3.7 V, 850 mAh, and 6.0 mm × 34.5 mm × 45.0 mm, and states that its lithium-polymer batteries include overcharge protection circuitry.
- [Jauch LP603443JU configured-pack material data sheet](https://www.jauch.com/downloadfile/677e3a8d45bcb384ed7454545825f7363/matd_246512_20200507_850mah_-_lp603443ju_1s1p_2_wire_70mm.pdf) — official example for a configured 850 mAh 1S1P pack. The ordered connector, polarity, wire exit, protection-PCB protrusion, and swelling envelope still require a project-specific delivery drawing.
- [Work Louder Creator Micro 2 official product page](https://worklouder.cc/creator-micro-2) — public exterior/function reference for a low round joystick-cap construction. It does not establish the unpublished Codex Micro internal component, circuit, or key count.

## Public Codex Micro experience references

These sources support only observable exterior/function decisions. They are not evidence for the unpublished MCU, circuit, dimensions, firmware, or protocol.

- [The Verge: OpenAI made a $230 keyboard to control Codex](https://www.theverge.com/ai-artificial-intelligence/965901/openai-hardware-codex-micro-launch) — public product imagery shows a wide microphone-labelled key immediately right of the circular touch control; reporting describes push-to-talk as a configurable command-key action.
- [Axios: OpenAI launches a keypad for AI agents](https://www.axios.com/2026/07/15/openai-keyboard-codex-agents) — independently reports customizable keys including a push-to-talk option.

Add official manufacturer data sheets for the selected:

- RGB LED and level shifter
- current-limited load switch
- exact keycap
- ESD/protection parts
- battery connector and the project-specific configured Li-Po delivery drawing
