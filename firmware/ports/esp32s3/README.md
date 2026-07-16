# ESP32-S3 ESP-IDF bench port

This directory intentionally contains a fail-closed host-compilable port stub, not a claimed device implementation. Select and record an ESP-IDF release before replacing its callbacks.

## Bring-up order

1. Add `firmware/common/include`, `firmware/boards/include`, and `firmware/common/src` to an ESP-IDF C++ component.
2. Replace `make_esp_idf_bench_stub()` with callbacks for a monotonic millisecond clock, MCP23017 I2C reads, direct D8/D9/D10 encoder GPIO reads, RGB rail enable, the 12-pixel output, and a 64-byte Vendor HID/control transport.
3. Bind pins only through `agent_deck::boards::kXiaoEsp32s3Plus`; keep D16 inside the adapter battery-sense implementation.
4. Leave `RGB_PWR_EN` off until GPIO direction and its external default-off pull are confirmed.
5. Run the host suite first, then record on-device evidence for boot straps, USB enumeration, encoder loss under traffic, RGB current, reconnect, and battery sensing.

The stub returns `false` for every hardware operation so accidentally linking it into a target cannot assert that an operation succeeded.
