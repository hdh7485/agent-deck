# Agent Deck repository contract

이 파일은 이 저장소에서 작업하는 사람과 AI 에이전트가 따라야 할 프로젝트별 규칙이다. 상위 실행 환경의 안전·검증 규칙을 대체하지 않는다.

## Product boundary

- 공개되지 않은 OpenAI Micro의 내부 MCU, 회로, 기구 치수, 펌웨어, 통신 프로토콜을 사실처럼 단정하지 않는다.
- 공개 제품은 사용자 경험을 정의하는 참고 자료일 뿐이다. 이 저장소는 독자적인 회로와 프로토콜을 설계한다.
- OLED나 LCD를 추가하지 않는다.
- 기계식 키, RGB LED, 엔코더, 내비게이션 스위치, 터치 전극은 모두 입력 PCB에 고정한다.
- 브레드보드는 초기 부품 단위 전기 검증에만 사용할 수 있으며 최종 입력 어셈블리로 취급하지 않는다.
- XIAO ESP32-S3 Plus와 XIAO nRF52840 Plus는 핀 호환 보드로 가정하지 않는다.

## Evidence rules

- MCU 핀, 전압, 전류, USB, 부트, 충전 회로에 관한 주장은 제조사 공식 위키·회로도·데이터시트로 검증한다.
- 핀맵 표를 바꾸면 `docs/hardware/pin-compatibility.md`와 `docs/research/source-register.md`를 함께 갱신한다.
- 공식 문서끼리 모순되면 더 보수적인 제한을 적용하고, 모순과 필요한 실측을 문서화한다.
- 유통 재고와 가격은 주문 직전 다시 확인한다. 특정 판매처의 현재 재고를 영구 사실로 기록하지 않는다.
- 확인되지 않은 기능과 수치는 `가정`, `후보`, `실측 필요` 중 하나로 표시한다.

## Locked V1 constraints

- 13 keys with one addressable RGB LED per key, one EC11-class encoder with click, one 5-way digital navigation switch, and one circular capacitive touch electrode.
- Common input PCB plus one MCU-specific adapter for each XIAO candidate.
- The XIAO onboard USB-C connector is exposed in V1; a second USB-C connector is not added without an explicit USB routing review.
- D16 is reserved for each board's battery sensing path and is not allocated as a generic output.
- Encoder A/B edges stay on direct MCU GPIO.
- Destructive host actions are semantic intents checked by the PC bridge, not raw Enter or arbitrary key injection.

## Change discipline

- Hardware changes require a short decision record in `docs/decisions/` when they affect PCB interfaces, power rails, safety, firmware abstractions, or enclosure constraints.
- Do not add a new dependency if a current tool or standard library covers the requirement.
- Shared device messages are specified first in `docs/protocol/device-protocol.md`; firmware and bridge implementations follow that document.
- Hardware net names are semantic (`ENC_A`, `IOX_INT`, `RGB_DATA`) and must not encode one MCU's GPIO number.
- MCU pin mappings live in adapter definitions, not in common input logic.
- Generated KiCad output, firmware build artifacts, captures containing secrets, and local environment files are not committed.

## Required verification

Before merging a hardware revision:

1. KiCad ERC and DRC pass with reviewed waivers only.
2. Power-path, maximum current, reverse-current, ESD, and battery cases are reviewed.
3. Connector orientation and XIAO bottom-pad mapping are checked against official drawings.
4. Plate, enclosure, encoder, joystick, and USB clearances are checked in 3D.
5. The applicable checks in `.omx/plans/test-spec-agent-deck-v1.md` have evidence attached.

Before merging firmware or bridge behavior:

1. Protocol codec tests pass on both ends.
2. Input events are debounced and do not duplicate across reconnects.
3. USB/BLE reconnect and transport failover are tested on supported hosts.
4. Approval, rejection, interruption, push, deploy, and deletion paths enforce state-aware confirmation.
5. The changed target builds without warnings treated as errors where the toolchain supports it.
