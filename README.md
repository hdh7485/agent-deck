# Agent Deck

Codex, Hermes, OMX, tmux 같은 AI 에이전트 작업을 물리적으로 제어하고 상태를 RGB로 표시하는 데스크톱 컨트롤러 프로젝트입니다.

이 프로젝트는 공개된 제품 경험을 참고하되, 공개되지 않은 OpenAI Micro의 회로·펌웨어·프로토콜을 추정하거나 복제하지 않습니다. 목표는 기능적으로 유사한 사용자 경험을 제공하는 독자 설계입니다.

## V1 범위

- PCB 고정형 기계식 키 13개와 키별 다이오드
- RGB 상태 표시 키 6개
- 클릭 가능한 로터리 엔코더 1개
- 5방향 디지털 내비게이션 스위치 1개
- 단일 원형 정전식 터치 패드 1개
- XIAO ESP32-S3 Plus와 XIAO nRF52840 Plus 비교 평가
- USB HID, Vendor HID, BLE HID 및 상태 통신 실험
- Codex/Hermes/OMX/tmux 상태를 정규화하는 PC 브리지
- USB 전원 우선 검증 후 1셀 Li-Po 평가

OLED나 LCD는 사용하지 않습니다. 모든 입력 부품은 브레드보드가 아니라 입력 PCB에 직접 실장합니다.

## 현재 기준 설계

V1은 공용 입력 PCB와 MCU별 어댑터 보드를 사용합니다. 입력 PCB에는 키 매트릭스, MCP23017, 내비게이션 스위치, 정전식 터치 IC, 엔코더, RGB LED 및 전원 보호 회로를 두고, 어댑터는 XIAO 보드별 핀·전원·USB 차이를 흡수합니다.

- 키 13개: 다이오드를 포함한 4×4 매트릭스
- MCP23017: 키 매트릭스, 5방향 스위치, 터치 출력 처리
- 엔코더 A/B/클릭: MCU 직접 연결
- 터치: AT42QT1010 계열 외부 IC 우선
- RGB: 5V 주소 지정 LED, 74AHCT1G125 레벨 시프터, 전류 제한 전원 스위치
- USB-C: V1에서는 장착한 XIAO의 온보드 USB-C를 케이스 밖으로 노출
- 배터리: 어댑터 측에서 각 XIAO의 충전·배터리 회로를 사용하고 공용 PCB에 충전기를 중복하지 않음

이 결정은 회로도 작성 전 공식 회로도 대조와 벤치 실험으로 다시 검증합니다.

## 문서 지도

- [제품 요구사항](.omx/plans/prd-agent-deck-v1.md)
- [검증 계획](.omx/plans/test-spec-agent-deck-v1.md)
- [시스템 아키텍처](docs/architecture/system-architecture.md)
- [XIAO 핀 호환성](docs/hardware/pin-compatibility.md)
- [전기 설계 제안](docs/hardware/electrical-proposal.md)
- [부품·기구 결정 체크리스트](docs/hardware/design-inputs-checklist.md)
- [V1 프로토타입 BOM](docs/hardware/prototype-bom.csv)
- [장치 프로토콜](docs/protocol/device-protocol.md)
- [공식 자료 목록](docs/research/source-register.md)
- [KiCad 구조](hardware/kicad/README.md)
- [펌웨어 구조](firmware/README.md)
- [PC 브리지 구조](bridge/README.md)
- [기구 설계 구조](mechanical/README.md)

## 제작 순서

1. 두 MCU의 최소 펌웨어와 통신 경로를 개발 보드에서 검증
2. 공식 핀맵·회로도와 선택 부품 데이터시트로 회로도 작성
3. 입력 PCB와 MCU 어댑터 PCB 설계 및 DRC/ERC
4. 스위치 플레이트 설계
5. 케이스와 USB/안테나/배터리 간섭 검증
6. 조립 및 전기적 안전 검사
7. USB/BLE/입력/RGB/전력/재연결/위험 동작 E2E 테스트

## 상태

현재는 V1 설계 입력과 검증 계획을 고정한 단계입니다. 실제 KiCad 회로와 펌웨어는 아직 시작하지 않았습니다.

