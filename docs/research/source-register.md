# Official source register

Accessed: 2026-07-16

These links are the evidence baseline for board-level claims. Before schematic release, record the revision printed on each purchased board and download the matching official schematic locally for review. Links may move; do not substitute reseller pinout images for the official sources.

## Seeed Studio XIAO ESP32-S3 Plus

- [Official XIAO ESP32-S3 Series wiki](https://wiki.seeedstudio.com/xiao_esp32s3_getting_started/) — Plus D0–D19 map, power pins, strapping caution, boot/reset, battery behavior, and official design resource links.
- [Official XIAO ESP32-S3 Plus schematic PDF](https://files.seeedstudio.com/wiki/SeeedStudio-XIAO-ESP32S3/res/XIAO_ESP32S3_Plus_SCH_PDF.pdf) — board nets, battery/charger, bottom pads, USB, and XIAO headers. Search result identified V1.1 dated 2025-07-24; confirm against the exact downloaded file at design freeze.
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

Add official manufacturer data sheets for the selected:

- MCP23017 package/revision
- touch controller and sensitivity network
- RGB LED and level shifter
- current-limited load switch
- hot-swap socket and mechanical switch
- encoder and five-way navigation switch
- adapter connector
- ESD/protection parts
- Li-Po cell and connector

