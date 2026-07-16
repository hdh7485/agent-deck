# nRF52840 Zephyr bench port

This directory intentionally contains a fail-closed host-compilable port stub, not a claimed device implementation. Select and record a Zephyr/nRF Connect SDK release before replacing its callbacks.

## Bring-up order

1. Add `firmware/common/include`, `firmware/boards/include`, and `firmware/common/src` to a Zephyr C++ library.
2. Replace `make_zephyr_bench_stub()` with callbacks for uptime, MCP23017 I2C reads, direct D8/D9/D10 encoder GPIO reads, RGB rail enable, the 12-pixel output, and USB Vendor HID/custom GATT control transports.
3. Bind pins only through `agent_deck::boards::kXiaoNrf52840Plus`; keep D16 and its board-specific read-enable sequence inside the adapter implementation.
4. Leave NFC-capable D14/D15 unused in the V1 common interface.
5. Run the host suite first, then record on-device evidence for USB, BLE bonding/reconnect, interrupt wake, encoder loss under traffic, RGB current, and battery sensing.

The stub returns `false` for every hardware operation so accidentally linking it into a target cannot assert that an operation succeeded.
