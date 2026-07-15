# XIAO Plus pin compatibility baseline

## Conclusion

The two Plus boards share many D-pin positions, but they are not drop-in electrical equivalents. V1 may use a conservative common subset through separate adapter boards. It must not connect every similarly named pad directly to the common input PCB.

This table was prepared from Seeed Studio's official board wiki and schematics, then cross-checked against the Espressif ESP32-S3 and Nordic nRF52840 official pin documentation. Exact purchased board revision must be checked again before schematic release.

## Position-by-position comparison

| XIAO position | ESP32-S3 Plus chip pin | nRF52840 Plus chip pin | Conservative shared use | V1 policy |
| --- | --- | --- | --- | --- |
| D0 | GPIO1, ADC | P0.02, AIN0 | Digital GPIO, ADC on both | `RGB_DATA` output |
| D1 | GPIO2, ADC | P0.03, AIN1 | Digital GPIO, ADC on both | `IOX_INT` input |
| D2 | GPIO3, ADC, ESP strapping/JTAG-source pin | P0.28, AIN4 | Digital/ADC electrically possible, boot semantics differ | Leave unconnected by default |
| D3 | GPIO4, ADC | P0.29, AIN5 | Digital GPIO, ADC on both | `RGB_PWR_EN` output with external default-off pull |
| D4 | GPIO5, I2C SDA, ADC | P0.04, I2C SDA, AIN2 | I2C SDA | `I2C_SDA` |
| D5 | GPIO6, I2C SCL, ADC | P0.05, I2C SCL, AIN3 | I2C SCL | `I2C_SCL` |
| D6 | GPIO43, UART TX | P1.11, UART TX | Digital GPIO/UART | Optional debug TX/test pad |
| D7 | GPIO44, UART RX | P1.12, UART RX | Digital GPIO/UART | Optional debug RX/test pad |
| D8 | GPIO7, SPI SCK, ADC | P1.13, SPI SCK | Digital GPIO/SPI; ADC only on ESP side | `ENC_A` input |
| D9 | GPIO8, SPI MISO, ADC | P1.14, SPI MISO | Digital GPIO/SPI; ADC only on ESP side | `ENC_B` input |
| D10 | GPIO9, SPI MOSI, ADC | P1.15, SPI MOSI | Digital GPIO/SPI; ADC only on ESP side | `ENC_SW` input |
| D11 | GPIO38; Seeed table says ADC but Espressif does not list an ADC channel | P0.15/I2S_SD; Seeed table says ADC but Nordic does not name it AIN | Digital GPIO only pending discrepancy resolution | Adapter spare, no analog claim |
| D12 | GPIO39, JTAG MTCK | P0.19/I2S_SCK | Digital GPIO, board-specific debug/peripheral roles | Adapter spare |
| D13 | GPIO40, JTAG MTDO | P1.01/I2S_WS | Digital GPIO, board-specific debug/peripheral roles | Adapter spare |
| D14 | GPIO41, JTAG MTDI | P0.09, NFC1/UART1 RX | Digital use requires board-specific configuration | Avoid on common PCB |
| D15 | GPIO42, JTAG MTMS | P0.10, NFC2/UART1 TX | Digital use requires board-specific configuration | Avoid on common PCB |
| D16 | GPIO10, board `ADC_BAT` | P0.31/AIN7, board battery sense | Battery sensing only; circuitry and enable semantics differ | Reserved, never generic output |
| D17 | GPIO13 | P1.03/SPI1 SCK | Digital GPIO | Optional adapter-local use |
| D18 | GPIO12 | P1.05/SPI1 MISO | Digital GPIO | Optional adapter-local use |
| D19 | GPIO11 | P1.07/SPI1 MOSI | Digital GPIO | Optional adapter-local use |

## Power and USB

| Function | ESP32-S3 Plus | nRF52840 Plus | Rule |
| --- | --- | --- | --- |
| VBUS/5V | USB-derived 5 V; Seeed documents special care for external injection | USB-derived 5 V/power pin | Treat as adapter power input, not a generic bidirectional rail |
| 3V3 | Regulated board output | Regulated board output | Common low-power logic rail only after current-budget review |
| Battery | Onboard charge/power circuit, board `ADC_BAT` on D16 | Onboard charge circuit, read enable plus D16 battery ADC path | Battery connector and sensing stay adapter-specific |
| USB | Native USB is wired to the onboard USB-C; relevant USB pads are board-specific | Native USB is wired to the onboard USB-C; bottom-pad routing must be checked from schematic | V1 exposes the onboard connector instead of adding a second connector |
| Reset/boot | ESP `CHIP_PU`, boot strap GPIO0; GPIO3 is also a strap | nRF reset/bootloader behavior and SWD | Expose adapter-specific service pads/buttons |

## Proposed common adapter interface

| Semantic signal | Default XIAO position | Direction at MCU | Notes |
| --- | --- | --- | --- |
| `RGB_DATA` | D0 | Output | Drives 74AHCT1G125 input, not LED directly |
| `IOX_INT` | D1 | Input | MCP23017 open-drain interrupt with 3.3 V pull-up |
| `RGB_PWR_EN` | D3 | Output | External pull-down keeps LED power off during reset |
| `I2C_SDA` | D4 | Bidirectional | MCP23017 bus, 3.3 V pull-up on common PCB |
| `I2C_SCL` | D5 | Output/open-drain | Same bus |
| `UART_TX_DBG` | D6 | Output | Optional test pad, not required in product mode |
| `UART_RX_DBG` | D7 | Input | Optional test pad, not required in product mode |
| `ENC_A` | D8 | Input | Direct MCU GPIO, hardware/software debounce study |
| `ENC_B` | D9 | Input | Direct MCU GPIO |
| `ENC_SW` | D10 | Input | Direct MCU GPIO |
| `3V3` | 3V3 | Power | MCP23017, touch IC, logic side of control circuits |
| `VBUS_5V` | 5V | Power | USB-mode RGB source only in baseline V1 |
| `GND` | GND | Power | Multiple connector contacts preferred |

D2 and D11–D19 are not required by the common PCB. Adapter revisions may use them only after documenting the board-specific reason.

## Required bench checks

1. Verify no common-PCB pull or capacitance changes ESP32-S3 boot behavior.
2. Verify MCP23017 interrupt wake behavior on both MCU sleep implementations.
3. Verify encoder counts on D8–D10 while USB/BLE traffic and RGB updates are active.
4. Verify D16 battery reading with the exact official board revision and documented enable sequence.
5. Verify the onboard USB-C connector can support the intended composite descriptors on both firmware stacks.

## Sources

See `docs/research/source-register.md`. Source conflict resolution is intentionally conservative: if a board wiki labels a pin as ADC but the silicon vendor does not expose an AIN/ADC channel on that chip pin, V1 treats it as digital only.

