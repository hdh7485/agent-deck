"""Deterministic 12-key LED snapshot generation."""

from __future__ import annotations

from typing import Mapping

from .core import SessionRegistry
from .protocol import (
    BatteryDisplayMode,
    ModeCode,
    NormalizedState,
    StateSnapshotPayload,
)


class LedRenderer:
    def __init__(
        self,
        colors: Mapping[NormalizedState, tuple[int, int, int]],
        *,
        led_count: int = 12,
    ) -> None:
        if not 1 <= led_count <= 12:
            raise ValueError("protocol v1 supports 1..12 snapshot LEDs")
        missing = set(NormalizedState) - set(colors)
        if missing:
            raise ValueError(f"missing LED colors for {sorted(item.name for item in missing)}")
        self.colors = dict(colors)
        self.led_count = led_count

    def snapshot(
        self,
        registry: SessionRegistry,
        *,
        connection_epoch: int,
        brightness_percent: int,
        mode: ModeCode = ModeCode.DEFAULT,
        battery_display_mode: BatteryDisplayMode = BatteryDisplayMode.ON_CHANGE,
    ) -> StateSnapshotPayload:
        selected = registry.selected()
        sessions = registry.sessions[: self.led_count]
        leds: list[tuple[int, int, int]] = []
        if not sessions:
            leds.append(self.colors[NormalizedState.DISCONNECTED])
        for session in sessions:
            color = self.colors[session.state]
            if selected is None or session.session_id != selected.session_id:
                color = tuple(round(channel * 0.4) for channel in color)
            leds.append(color)
        while len(leds) < self.led_count:
            leds.append((0, 0, 0))
        return StateSnapshotPayload(
            epoch=connection_epoch,
            selected_session_id=selected.session_id if selected else 0,
            state_version=selected.state_version if selected else 0,
            brightness_percent=brightness_percent,
            mode=mode,
            battery_display_mode=battery_display_mode,
            leds=tuple(leds),
        )
