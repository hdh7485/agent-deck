#!/usr/bin/env python3
"""Generate the Agent Deck V1 KiCad engineering draft.

Run this script with KiCad's bundled Python interpreter.  The generated boards
are intentionally reproducible: the common input PCB contains the complete V1
electrical net assignment, while the two adapter boards isolate board-specific
XIAO pin mappings.

This is an engineering draft, not fabrication release data.  The exact MX
switch/socket, navigation switch, connector stack height, and touch tuning
values remain mechanical/electrical validation inputs.
"""

from __future__ import annotations

import json
import math
import sys
import uuid
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[3]
KICAD_ROOT = Path("/opt/homebrew/Caskroom/kicad/10.0.4/KiCad/KiCad.app/Contents/SharedSupport")
FP_ROOT = KICAD_ROOT / "footprints"
OUT_ROOT = ROOT / "hardware" / "kicad"
RENDER_ROOT = ROOT / "artifacts" / "renders"


def mm(value: float) -> int:
    return pcbnew.FromMM(value)


def pt(x: float, y: float) -> pcbnew.VECTOR2I:
    return pcbnew.VECTOR2I(mm(x), mm(y))


def xy(position: pcbnew.VECTOR2I) -> tuple[float, float]:
    return pcbnew.ToMM(position.x), pcbnew.ToMM(position.y)


def ensure_dirs() -> None:
    for path in (
        OUT_ROOT / "input-main",
        OUT_ROOT / "adapters" / "xiao-esp32s3-plus",
        OUT_ROOT / "adapters" / "xiao-nrf52840-plus",
        OUT_ROOT / "libraries" / "agent-deck.pretty",
        RENDER_ROOT,
    ):
        path.mkdir(parents=True, exist_ok=True)


def add_net(board: pcbnew.BOARD, name: str) -> pcbnew.NETINFO_ITEM:
    net = pcbnew.NETINFO_ITEM(board, name)
    board.Add(net)
    return net


def net_map(board: pcbnew.BOARD, names: list[str]) -> dict[str, pcbnew.NETINFO_ITEM]:
    return {name: add_net(board, name) for name in names}


def load_footprint(lib: str, name: str) -> pcbnew.FOOTPRINT:
    footprint = pcbnew.FootprintLoad(str(FP_ROOT / f"{lib}.pretty"), name)
    if footprint is None:
        raise RuntimeError(f"Unable to load footprint {lib}:{name}")
    return footprint


def place_footprint(
    board: pcbnew.BOARD,
    footprint: pcbnew.FOOTPRINT,
    reference: str,
    value: str,
    x: float,
    y: float,
    *,
    angle: float = 0,
    back: bool = False,
) -> pcbnew.FOOTPRINT:
    footprint.SetReference(reference)
    footprint.SetValue(value)
    footprint.SetPosition(pt(x, y))
    footprint.SetOrientationDegrees(angle)
    board.Add(footprint)
    if back:
        footprint.Flip(footprint.GetPosition(), False)
    try:
        footprint.Reference().SetVisible(True)
        footprint.Value().SetVisible(False)
    except AttributeError:
        pass
    return footprint


def assign_pads(
    footprint: pcbnew.FOOTPRINT,
    nets: dict[str, pcbnew.NETINFO_ITEM],
    assignments: dict[str, str | None],
) -> None:
    for pad in footprint.Pads():
        number = pad.GetNumber()
        if number in assignments and assignments[number] is not None:
            pad.SetNet(nets[assignments[number]])


def pad_by_number(footprint: pcbnew.FOOTPRINT, number: str) -> pcbnew.PAD:
    for pad in footprint.Pads():
        if pad.GetNumber() == number:
            return pad
    raise KeyError(f"{footprint.GetReference()} has no pad {number}")


def add_track(
    board: pcbnew.BOARD,
    net: pcbnew.NETINFO_ITEM,
    start: tuple[float, float] | pcbnew.VECTOR2I,
    end: tuple[float, float] | pcbnew.VECTOR2I,
    *,
    layer: int = pcbnew.B_Cu,
    width: float = 0.25,
) -> pcbnew.PCB_TRACK:
    track = pcbnew.PCB_TRACK(board)
    track.SetNet(net)
    track.SetLayer(layer)
    track.SetWidth(mm(width))
    track.SetStart(start if isinstance(start, pcbnew.VECTOR2I) else pt(*start))
    track.SetEnd(end if isinstance(end, pcbnew.VECTOR2I) else pt(*end))
    board.Add(track)
    return track


def add_path(
    board: pcbnew.BOARD,
    net: pcbnew.NETINFO_ITEM,
    points: list[tuple[float, float] | pcbnew.VECTOR2I],
    *,
    layer: int = pcbnew.B_Cu,
    width: float = 0.25,
) -> None:
    for start, end in zip(points, points[1:]):
        add_track(board, net, start, end, layer=layer, width=width)


def add_via(
    board: pcbnew.BOARD,
    net: pcbnew.NETINFO_ITEM,
    position: tuple[float, float] | pcbnew.VECTOR2I,
    *,
    diameter: float = 0.8,
    drill: float = 0.4,
) -> pcbnew.PCB_VIA:
    via = pcbnew.PCB_VIA(board)
    via.SetNet(net)
    via.SetPosition(position if isinstance(position, pcbnew.VECTOR2I) else pt(*position))
    via.SetWidth(mm(diameter))
    via.SetDrill(mm(drill))
    via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    board.Add(via)
    return via


def add_board_line(
    board: pcbnew.BOARD,
    start: tuple[float, float],
    end: tuple[float, float],
    *,
    layer: int = pcbnew.Edge_Cuts,
    width: float = 0.2,
) -> None:
    line = pcbnew.PCB_SHAPE(board)
    line.SetShape(pcbnew.SHAPE_T_SEGMENT)
    line.SetStart(pt(*start))
    line.SetEnd(pt(*end))
    line.SetLayer(layer)
    line.SetWidth(mm(width))
    board.Add(line)


def add_rect_outline(board: pcbnew.BOARD, left: float, top: float, right: float, bottom: float, chamfer: float = 3.0) -> None:
    points = [
        (left + chamfer, top),
        (right - chamfer, top),
        (right, top + chamfer),
        (right, bottom - chamfer),
        (right - chamfer, bottom),
        (left + chamfer, bottom),
        (left, bottom - chamfer),
        (left, top + chamfer),
        (left + chamfer, top),
    ]
    for start, end in zip(points, points[1:]):
        add_board_line(board, start, end)


def add_text(
    board: pcbnew.BOARD,
    text_value: str,
    x: float,
    y: float,
    *,
    layer: int = pcbnew.F_SilkS,
    size: float = 1.2,
    thickness: float = 0.2,
    angle: float = 0,
) -> pcbnew.PCB_TEXT:
    text = pcbnew.PCB_TEXT(board)
    text.SetText(text_value)
    text.SetPosition(pt(x, y))
    text.SetLayer(layer)
    text.SetTextSize(pt(size, size))
    text.SetTextThickness(mm(thickness))
    text.SetTextAngleDegrees(angle)
    if layer in (pcbnew.B_SilkS, pcbnew.B_Cu, pcbnew.B_Fab):
        text.SetMirrored(True)
    board.Add(text)
    return text


def add_zone(
    board: pcbnew.BOARD,
    net: pcbnew.NETINFO_ITEM,
    layer: int,
    points: list[tuple[float, float]],
    *,
    clearance: float = 0.25,
    min_thickness: float = 0.25,
) -> pcbnew.ZONE:
    zone = pcbnew.ZONE(board)
    zone.SetLayer(layer)
    zone.SetNet(net)
    zone.SetLocalClearance(mm(clearance))
    zone.SetMinThickness(mm(min_thickness))
    zone.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
    outline = zone.Outline()
    outline.NewOutline()
    for x, y in points:
        outline.Append(mm(x), mm(y))
    board.Add(zone)
    return zone


def add_mounting_hole(board: pcbnew.BOARD, reference: str, x: float, y: float) -> pcbnew.FOOTPRINT:
    fp = load_footprint("MountingHole", "MountingHole_3.2mm_M3")
    return place_footprint(board, fp, reference, "M3", x, y)


def add_smd_pad(
    footprint: pcbnew.FOOTPRINT,
    number: str,
    x: float,
    y: float,
    sx: float,
    sy: float,
    *,
    shape: int = pcbnew.PAD_SHAPE_ROUNDRECT,
    layer: int = pcbnew.F_Cu,
) -> pcbnew.PAD:
    pad = pcbnew.PAD(footprint)
    pad.SetNumber(number)
    pad.SetAttribute(pcbnew.PAD_ATTRIB_SMD)
    pad.SetShape(shape)
    pad.SetSize(pt(sx, sy))
    pad.SetPosition(pt(x, y))
    layers = pcbnew.LSET()
    layers.AddLayer(layer)
    layers.AddLayer(pcbnew.F_Paste if layer == pcbnew.F_Cu else pcbnew.B_Paste)
    layers.AddLayer(pcbnew.F_Mask if layer == pcbnew.F_Cu else pcbnew.B_Mask)
    pad.SetLayerSet(layers)
    if shape == pcbnew.PAD_SHAPE_ROUNDRECT:
        pad.SetRoundRectRadiusRatio(0.2)
    footprint.Add(pad)
    return pad


def add_th_pad(
    footprint: pcbnew.FOOTPRINT,
    number: str,
    x: float,
    y: float,
    diameter: float = 2.0,
    drill: float = 1.0,
    *,
    shape: int = pcbnew.PAD_SHAPE_CIRCLE,
) -> pcbnew.PAD:
    pad = pcbnew.PAD(footprint)
    pad.SetNumber(number)
    pad.SetAttribute(pcbnew.PAD_ATTRIB_PTH)
    pad.SetShape(shape)
    pad.SetSize(pt(diameter, diameter))
    pad.SetDrillSize(pt(drill, drill))
    pad.SetPosition(pt(x, y))
    pad.SetLayerSet(pad.PTHMask())
    footprint.Add(pad)
    return pad


def add_fp_line(
    footprint: pcbnew.FOOTPRINT,
    start: tuple[float, float],
    end: tuple[float, float],
    *,
    layer: int = pcbnew.F_SilkS,
    width: float = 0.2,
) -> None:
    line = pcbnew.PCB_SHAPE(footprint)
    line.SetShape(pcbnew.SHAPE_T_SEGMENT)
    line.SetStart(pt(*start))
    line.SetEnd(pt(*end))
    line.SetLayer(layer)
    line.SetWidth(mm(width))
    footprint.Add(line)


def make_navigation_footprint() -> pcbnew.FOOTPRINT:
    """Provisional six-contact footprint; final drawing requires chosen MPN."""
    fp = pcbnew.FOOTPRINT(None)
    fp.SetFPIDAsString("AgentDeck:Nav5_SKRHABE010_PROVISIONAL")
    fp.SetReference("NAV1")
    fp.SetValue("SKRHABE010 candidate - verify land pattern")
    for number, x, y in (
        ("1", 0, -4.5),
        ("2", 0, 4.5),
        ("3", -4.5, 0),
        ("4", 4.5, 0),
        ("5", 0, 0),
        ("6", 4.5, 4.5),
    ):
        add_th_pad(fp, number, x, y, 1.8, 0.9)
    for start, end in (
        ((-6.5, -6.5), (6.5, -6.5)),
        ((6.5, -6.5), (6.5, 6.5)),
        ((6.5, 6.5), (-6.5, 6.5)),
        ((-6.5, 6.5), (-6.5, -6.5)),
    ):
        add_fp_line(fp, start, end)
    return fp


def make_touch_electrode() -> pcbnew.FOOTPRINT:
    fp = pcbnew.FOOTPRINT(None)
    fp.SetFPIDAsString("AgentDeck:Touch_Electrode_14mm")
    fp.SetReference("E1")
    fp.SetValue("14 mm circular touch electrode")
    add_smd_pad(fp, "1", 0, 0, 14.0, 14.0, shape=pcbnew.PAD_SHAPE_CIRCLE)
    return fp


def make_testpoint(reference: str, value: str) -> pcbnew.FOOTPRINT:
    fp = load_footprint("TestPoint", "TestPoint_Pad_D1.5mm")
    fp.SetReference(reference)
    fp.SetValue(value)
    return fp


def make_xiao_plus_footprint() -> pcbnew.FOOTPRINT:
    """Physical pad pattern transcribed from Seeed's official Plus baseboard."""
    fp = pcbnew.FOOTPRINT(None)
    fp.SetFPIDAsString("AgentDeck:XIAO_Plus_Official_Base_Pattern")
    fp.SetReference("MOD1")
    fp.SetValue("Seeed XIAO Plus (official base pattern)")
    fp.SetAllowSolderMaskBridges(True)

    left_outer_y = (-7.62, -5.08, -2.54, 0, 2.54, 5.08, 7.62)
    right_outer_y = (7.62, 5.08, 2.54, 0, -2.54, -5.08, -7.62)
    for number, y in enumerate(left_outer_y, start=1):
        add_smd_pad(fp, str(number), -8.89, y, 2.032, 0.95)
    for number, y in enumerate(right_outer_y, start=8):
        add_smd_pad(fp, str(number), 8.89, y, 2.032, 0.95)

    for number, y in zip(range(15, 21), (-6.35, -3.81, -1.27, 1.27, 3.81, 6.35)):
        add_smd_pad(fp, str(number), -9.29, y, 1.232, 0.95)
    for number, y in zip(range(21, 24), (6.35, 3.81, 1.27)):
        add_smd_pad(fp, str(number), 9.29, y, 1.232, 0.95)

    for number, x, y in (
        (24, -1.27, -8.636),
        (25, 1.27, -8.636),
        (26, -1.27, -6.096),
        (27, 1.27, -6.096),
        (28, -1.27, -3.556),
        (29, 1.27, -3.556),
        (30, -1.27, -1.016),
        (31, 1.27, -1.016),
    ):
        add_smd_pad(fp, str(number), x, y, 1.7, 1.7)
    pad32 = add_smd_pad(fp, "32", -0.994, 5.518, 2.5, 1.1, shape=pcbnew.PAD_SHAPE_OVAL)
    pad33 = add_smd_pad(fp, "33", 1.006, 5.518, 2.5, 1.1, shape=pcbnew.PAD_SHAPE_OVAL)
    pad32.SetOrientationDegrees(270)
    pad33.SetOrientationDegrees(270)

    outline = [(-10.5, -11.5), (10.5, -11.5), (10.5, 11.5), (-10.5, 11.5), (-10.5, -11.5)]
    for start, end in zip(outline, outline[1:]):
        add_fp_line(fp, start, end, layer=pcbnew.F_SilkS, width=0.25)
    add_fp_line(fp, (-4, -11.5), (4, -11.5), layer=pcbnew.F_SilkS, width=0.8)
    return fp


def main_board() -> pcbnew.BOARD:
    board = pcbnew.BOARD()
    board.SetFileName(str(OUT_ROOT / "input-main" / "input-main.kicad_pcb"))

    net_names = [
        "GND",
        "+3V3",
        "VBUS_5V",
        "LED_5V",
        "I2C_SDA",
        "I2C_SCL",
        "IOX_INT",
        "IOX_INTA_TP",
        "RGB_DATA",
        "RGB_PWR_EN",
        "RGB_OE_N",
        "RGB_BUF_OUT",
        "RGB_DIN0",
        "RGB_FAULT_N",
        "RGB_ILIM",
        "ENC_A",
        "ENC_B",
        "ENC_SW",
        "UART_TX_DBG",
        "UART_RX_DBG",
        "SPARE0",
        "SPARE1",
        "NAV_UP_N",
        "NAV_DOWN_N",
        "NAV_LEFT_N",
        "NAV_RIGHT_N",
        "NAV_CENTER_N",
        "TOUCH_OUT",
        "TOUCH_ELECTRODE",
        "TOUCH_SNSK",
        "TOUCH_SNS",
    ]
    net_names += [f"ROW{i}" for i in range(4)]
    net_names += [f"COL{i}" for i in range(4)]
    net_names += [f"K{i}_D" for i in range(1, 14)]
    net_names += [f"RGB_LINK{i}" for i in range(1, 6)]
    nets = net_map(board, net_names)

    add_rect_outline(board, 10, 10, 142, 102, chamfer=4)
    for ref, x, y in (("H1", 15, 15), ("H2", 137, 15), ("H3", 15, 97), ("H4", 137, 97)):
        add_mounting_hole(board, ref, x, y)

    add_text(board, "AGENT DECK V1", 76, 13.5, size=1.8, thickness=0.3)
    add_text(board, "OPEN HARDWARE ENGINEERING DRAFT • NO DISPLAY", 76, 99, size=0.9)
    add_text(board, "TOUCH", 28, 94, size=1.0)
    add_text(board, "NAV", 116, 61, size=1.0)
    add_text(board, "ENCODER", 113, 36, size=1.0)
    add_text(board, "COMMON MCU ADAPTER", 131, 65, size=0.8, angle=90)
    add_text(board, "LOGIC / POWER - BACK", 103, 99, layer=pcbnew.B_SilkS, size=0.8)

    key_positions = [
        (28, 26),
        (47, 26),
        (66, 26),
        (85, 26),
        (28, 45),
        (47, 45),
        (66, 45),
        (85, 45),
        (28, 64),
        (47, 64),
        (66, 64),
        (85, 64),
        (85, 83),
    ]
    switches: list[pcbnew.FOOTPRINT] = []
    diodes: list[pcbnew.FOOTPRINT] = []
    leds: list[pcbnew.FOOTPRINT] = []
    for index, (x, y) in enumerate(key_positions, start=1):
        row = (index - 1) // 4
        col = 3 if index == 13 else (index - 1) % 4
        sw = place_footprint(
            board,
            load_footprint("Button_Switch_Keyboard", "SW_Cherry_MX_1.00u_Plate"),
            f"SW{index}",
            "MX 1u soldered prototype",
            x,
            y,
        )
        assign_pads(sw, nets, {"1": f"ROW{row}", "2": f"K{index}_D"})
        switches.append(sw)

        diode = place_footprint(
            board,
            load_footprint("Diode_SMD", "D_SOD-123"),
            f"D{index}",
            "1N4148W",
            x - 4.7,
            y + 9.0,
            angle=180,
            back=True,
        )
        assign_pads(diode, nets, {"1": f"K{index}_D", "2": f"COL{col}"})
        diodes.append(diode)

        sw2 = pad_by_number(sw, "2").GetPosition()
        d1 = pad_by_number(diode, "1").GetPosition()
        add_track(board, nets[f"K{index}_D"], sw2, d1, layer=pcbnew.B_Cu, width=0.3)

        if index <= 6:
            led = place_footprint(
                board,
                load_footprint("LED_SMD", "LED_SK6812MINI-E_3.2x2.8mm_P1.5mm_ReverseMount"),
                f"LED{index}",
                "SK6812MINI-E",
                x,
                y - 5.08,
                angle=90,
            )
            din = "RGB_DIN0" if index == 1 else f"RGB_LINK{index - 1}"
            dout = f"RGB_LINK{index}" if index < 6 else None
            assign_pads(led, nets, {"1": "LED_5V", "2": dout, "3": "GND", "4": din})
            leds.append(led)

    # Matrix buses. Rows use F.Cu, columns use B.Cu to keep crossings deterministic.
    for row in range(4):
        row_switches = [sw for i, sw in enumerate(switches, start=1) if (i - 1) // 4 == row]
        positions = [pad_by_number(sw, "1").GetPosition() for sw in row_switches]
        for start, end in zip(positions, positions[1:]):
            add_track(board, nets[f"ROW{row}"], start, end, layer=pcbnew.F_Cu, width=0.35)
    for col in range(4):
        col_diodes = [d for i, d in enumerate(diodes, start=1) if (3 if i == 13 else (i - 1) % 4) == col]
        positions = [pad_by_number(d, "2").GetPosition() for d in col_diodes]
        bus_x = key_positions[col][0] + 7.0
        for position in positions:
            _, position_y = xy(position)
            add_track(board, nets[f"COL{col}"], position, (bus_x, position_y), layer=pcbnew.B_Cu, width=0.35)
        if len(positions) > 1:
            first_y = xy(positions[0])[1]
            last_y = xy(positions[-1])[1]
            add_track(board, nets[f"COL{col}"], (bus_x, first_y), (bus_x, last_y), layer=pcbnew.B_Cu, width=0.35)

    # RGB data chain and local decoupling.
    for index, led in enumerate(leds, start=1):
        cap = place_footprint(
            board,
            load_footprint("Capacitor_SMD", "C_0603_1608Metric"),
            f"C{index}",
            "100nF LED local",
            key_positions[index - 1][0] + 11.5,
            key_positions[index - 1][1] - 5.0,
            back=True,
        )
        assign_pads(cap, nets, {"1": "LED_5V", "2": "GND"})

    encoder = place_footprint(
        board,
        load_footprint("Rotary_Encoder", "RotaryEncoder_Alps_EC11E-Switch_Vertical_H20mm"),
        "ENC1",
        "EC11E15244G1 candidate",
        105,
        22,
    )
    assign_pads(encoder, nets, {"A": "ENC_A", "B": "ENC_B", "C": "GND", "S1": "ENC_SW", "S2": "GND"})

    nav = place_footprint(board, make_navigation_footprint(), "NAV1", "SKRHABE010 candidate", 116, 50)
    assign_pads(
        nav,
        nets,
        {
            "1": "NAV_UP_N",
            "2": "NAV_DOWN_N",
            "3": "NAV_LEFT_N",
            "4": "NAV_RIGHT_N",
            "5": "NAV_CENTER_N",
            "6": "GND",
        },
    )

    electrode = place_footprint(board, make_touch_electrode(), "E1", "14 mm circular touch electrode", 28, 83)
    assign_pads(electrode, nets, {"1": "TOUCH_ELECTRODE"})

    mcp = place_footprint(
        board,
        load_footprint("Package_SO", "SOIC-28W_7.5x17.9mm_P1.27mm"),
        "U1",
        "MCP23017-E/SO",
        105,
        83,
        back=True,
    )
    assign_pads(
        mcp,
        nets,
        {
            "1": "NAV_UP_N",
            "2": "NAV_DOWN_N",
            "3": "NAV_LEFT_N",
            "4": "NAV_RIGHT_N",
            "5": "NAV_CENTER_N",
            "6": "TOUCH_OUT",
            "7": "SPARE0",
            "8": "SPARE1",
            "9": "+3V3",
            "10": "GND",
            "12": "I2C_SCL",
            "13": "I2C_SDA",
            "15": "GND",
            "16": "GND",
            "17": "GND",
            "18": "+3V3",
            "19": "IOX_INT",
            "20": "IOX_INTA_TP",
            "21": "ROW0",
            "22": "ROW1",
            "23": "ROW2",
            "24": "ROW3",
            "25": "COL0",
            "26": "COL1",
            "27": "COL2",
            "28": "COL3",
        },
    )

    touch = place_footprint(
        board,
        load_footprint("Package_TO_SOT_SMD", "SOT-23-6"),
        "U2",
        "AT42QT1010-TSHR",
        49,
        86,
        back=True,
    )
    assign_pads(
        touch,
        nets,
        {"1": "TOUCH_OUT", "2": "GND", "3": "TOUCH_SNSK", "4": "TOUCH_SNS", "5": "+3V3", "6": "GND"},
    )
    touch_rs = place_footprint(
        board,
        load_footprint("Resistor_SMD", "R_0603_1608Metric"),
        "R1",
        "1k touch series",
        39,
        84,
        back=True,
    )
    assign_pads(touch_rs, nets, {"1": "TOUCH_ELECTRODE", "2": "TOUCH_SNSK"})
    touch_cs = place_footprint(
        board,
        load_footprint("Capacitor_SMD", "C_0603_1608Metric"),
        "C20",
        "10nF C0G touch candidate",
        44,
        90,
        back=True,
    )
    assign_pads(touch_cs, nets, {"1": "TOUCH_SNSK", "2": "TOUCH_SNS"})
    touch_dec = place_footprint(
        board,
        load_footprint("Capacitor_SMD", "C_0603_1608Metric"),
        "C21",
        "100nF",
        52,
        90,
        back=True,
    )
    assign_pads(touch_dec, nets, {"1": "+3V3", "2": "GND"})

    rgb_switch = place_footprint(
        board,
        load_footprint("Package_TO_SOT_SMD", "SOT-23-6"),
        "U3",
        "TPS2553DBVR",
        76,
        95,
        back=True,
    )
    assign_pads(
        rgb_switch,
        nets,
        {"1": "VBUS_5V", "2": "GND", "3": "RGB_PWR_EN", "4": "RGB_FAULT_N", "5": "RGB_ILIM", "6": "LED_5V"},
    )
    rilim = place_footprint(
        board,
        load_footprint("Resistor_SMD", "R_0603_1608Metric"),
        "R2",
        "232k 1% ILIM (~117mA typ)",
        81,
        96,
        back=True,
    )
    assign_pads(rilim, nets, {"1": "RGB_ILIM", "2": "GND"})
    en_pd = place_footprint(
        board,
        load_footprint("Resistor_SMD", "R_0603_1608Metric"),
        "R3",
        "100k EN pulldown",
        71,
        96,
        back=True,
    )
    assign_pads(en_pd, nets, {"1": "RGB_PWR_EN", "2": "GND"})

    level = place_footprint(
        board,
        load_footprint("Package_TO_SOT_SMD", "SOT-23-5"),
        "U4",
        "SN74AHCT1G125DBVR",
        88,
        95,
        back=True,
    )
    assign_pads(level, nets, {"1": "RGB_OE_N", "2": "RGB_DATA", "3": "GND", "4": "RGB_BUF_OUT", "5": "VBUS_5V"})

    q1 = place_footprint(
        board,
        load_footprint("Package_TO_SOT_SMD", "SOT-23"),
        "Q1",
        "MMBT3904 RGB OE inverter",
        94,
        95,
        back=True,
    )
    assign_pads(q1, nets, {"1": "RGB_PWR_EN", "2": "GND", "3": "RGB_OE_N"})
    oe_pull = place_footprint(
        board,
        load_footprint("Resistor_SMD", "R_0603_1608Metric"),
        "R4",
        "10k OE pullup",
        99,
        96,
        back=True,
    )
    assign_pads(oe_pull, nets, {"1": "RGB_OE_N", "2": "VBUS_5V"})
    rgb_series = place_footprint(
        board,
        load_footprint("Resistor_SMD", "R_0603_1608Metric"),
        "R5",
        "330R RGB data",
        62,
        94,
        back=True,
    )
    assign_pads(rgb_series, nets, {"1": "RGB_BUF_OUT", "2": "RGB_DIN0"})

    bulk = place_footprint(
        board,
        load_footprint("Capacitor_THT", "C_Radial_D8.0mm_H11.5mm_P3.50mm"),
        "C30",
        "470uF 10V RGB bulk",
        47,
        95,
        angle=90,
    )
    assign_pads(bulk, nets, {"1": "LED_5V", "2": "GND"})

    # I2C pull-ups and logic decoupling.
    for ref, value, x, net_name in (
        ("R6", "4.7k SDA pullup", 111, "I2C_SDA"),
        ("R7", "4.7k SCL pullup", 115, "I2C_SCL"),
    ):
        resistor = place_footprint(
            board,
            load_footprint("Resistor_SMD", "R_0603_1608Metric"),
            ref,
            value,
            x,
            96,
            back=True,
        )
        assign_pads(resistor, nets, {"1": "+3V3", "2": net_name})
    mcp_dec = place_footprint(
        board,
        load_footprint("Capacitor_SMD", "C_0603_1608Metric"),
        "C22",
        "100nF MCP23017",
        119,
        96,
        back=True,
    )
    assign_pads(mcp_dec, nets, {"1": "+3V3", "2": "GND"})

    connector = place_footprint(
        board,
        load_footprint("Connector_PinSocket_2.54mm", "PinSocket_2x10_P2.54mm_Vertical"),
        "J1",
        "COMMON_MCU_ADAPTER_2x10",
        128,
        68,
        back=True,
    )
    common_connector_map = {
        "1": "+3V3",
        "2": "GND",
        "3": "VBUS_5V",
        "4": "GND",
        "5": "I2C_SDA",
        "6": "I2C_SCL",
        "7": "IOX_INT",
        "8": "RGB_DATA",
        "9": "RGB_PWR_EN",
        "10": "ENC_A",
        "11": "ENC_B",
        "12": "ENC_SW",
        "13": "UART_TX_DBG",
        "14": "UART_RX_DBG",
        "15": "SPARE0",
        "16": "SPARE1",
        "17": "GND",
        "18": "GND",
        "19": "GND",
        "20": "GND",
    }
    assign_pads(connector, nets, common_connector_map)

    # Long routes remain as ratsnest in this engineering draft.  The first
    # autoroute experiment was removed after DRC found genuine crossings;
    # manual routing starts only after the mechanical parts are locked.

    # Back ground plane and front 3V3 plane. Power rail islands and signal
    # clearances are checked by KiCad; final release will add tuned stitching.
    zone_points = [(11, 11), (141, 11), (141, 101), (11, 101)]
    add_zone(board, nets["GND"], pcbnew.B_Cu, zone_points, clearance=0.3)
    add_zone(board, nets["+3V3"], pcbnew.F_Cu, zone_points, clearance=0.3)

    # Touch keep-out guidance on User.Drawings (not an electrical keepout yet).
    radius = 11.5
    for angle in range(0, 360, 15):
        a1 = math.radians(angle)
        a2 = math.radians(angle + 15)
        add_board_line(
            board,
            (28 + radius * math.cos(a1), 83 + radius * math.sin(a1)),
            (28 + radius * math.cos(a2), 83 + radius * math.sin(a2)),
            layer=pcbnew.Dwgs_User,
            width=0.15,
        )
    add_text(board, "TOUCH QUIET ZONE", 28, 70.5, layer=pcbnew.Dwgs_User, size=0.7)
    add_text(board, "PLACEMENT / NETLIST DRAFT - NOT FAB READY", 76, 16.3, layer=pcbnew.F_SilkS, size=0.7)

    # Zone filling is deferred to KiCad proper.  The macOS pcbnew Python module
    # requires a GUI app object for its zone filler and can crash headless.
    return board


def xiao_adapter_board(board_name: str, subtitle: str) -> pcbnew.BOARD:
    board = pcbnew.BOARD()
    out_dir = OUT_ROOT / "adapters" / board_name
    board.SetFileName(str(out_dir / f"{board_name}.kicad_pcb"))
    names = [
        "GND",
        "+3V3",
        "VBUS_5V",
        "I2C_SDA",
        "I2C_SCL",
        "IOX_INT",
        "RGB_DATA",
        "RGB_PWR_EN",
        "ENC_A",
        "ENC_B",
        "ENC_SW",
        "UART_TX_DBG",
        "UART_RX_DBG",
        "SPARE0",
        "SPARE1",
        "BAT_SENSE_D16_RESERVED",
    ]
    nets = net_map(board, names)
    add_rect_outline(board, 10, 10, 86, 48, chamfer=2.5)
    for ref, x, y in (("H1", 14, 14), ("H2", 82, 14), ("H3", 14, 44), ("H4", 82, 44)):
        add_mounting_hole(board, ref, x, y)
    add_text(board, "AGENT DECK MCU ADAPTER", 48, 12.5, size=1.15)
    add_text(board, subtitle, 48, 46, size=0.85)
    add_text(board, "ONBOARD USB-C →", 20, 29, size=0.75, angle=90)
    add_text(board, "D16 BAT SENSE ONLY", 38, 43.2, layer=pcbnew.B_SilkS, size=0.65)

    xiao = place_footprint(board, make_xiao_plus_footprint(), "MOD1", subtitle, 31, 29, angle=90)
    xiao_map = {
        "1": "RGB_DATA",
        "2": "IOX_INT",
        "4": "RGB_PWR_EN",
        "5": "I2C_SDA",
        "6": "I2C_SCL",
        "7": "UART_TX_DBG",
        "8": "UART_RX_DBG",
        "9": "ENC_A",
        "10": "ENC_B",
        "11": "ENC_SW",
        "12": "+3V3",
        "13": "GND",
        "14": "VBUS_5V",
        "20": "BAT_SENSE_D16_RESERVED",
        "27": "GND",
        "33": "GND",
    }
    assign_pads(xiao, nets, xiao_map)

    connector = place_footprint(
        board,
        load_footprint("Connector_PinHeader_2.54mm", "PinHeader_2x10_P2.54mm_Vertical"),
        "J1",
        "COMMON_MCU_ADAPTER_2x10",
        74,
        17,
        angle=270,
    )
    connector_map = {
        "1": "+3V3",
        "2": "GND",
        "3": "VBUS_5V",
        "4": "GND",
        "5": "I2C_SDA",
        "6": "I2C_SCL",
        "7": "IOX_INT",
        "8": "RGB_DATA",
        "9": "RGB_PWR_EN",
        "10": "ENC_A",
        "11": "ENC_B",
        "12": "ENC_SW",
        "13": "UART_TX_DBG",
        "14": "UART_RX_DBG",
        "15": "SPARE0",
        "16": "SPARE1",
        "17": "GND",
        "18": "GND",
        "19": "GND",
        "20": "GND",
    }
    assign_pads(connector, nets, connector_map)

    add_text(board, "PLACEMENT / NETLIST DRAFT", 68, 45, layer=pcbnew.B_SilkS, size=0.6)

    # Reserved D16 is intentionally isolated and exposed only as a test pad.
    d16_tp = place_footprint(board, make_testpoint("TP1", "D16_BAT_SENSE_RESERVED"), "TP1", "D16 reserved", 39, 42, back=True)
    assign_pads(d16_tp, nets, {"1": "BAT_SENSE_D16_RESERVED"})
    add_via(board, nets["BAT_SENSE_D16_RESERVED"], pad_by_number(xiao, "20").GetPosition())
    add_track(board, nets["BAT_SENSE_D16_RESERVED"], pad_by_number(xiao, "20").GetPosition(), pad_by_number(d16_tp, "1").GetPosition(), layer=pcbnew.B_Cu)

    zone_points = [(11, 11), (85, 11), (85, 47), (11, 47)]
    add_zone(board, nets["GND"], pcbnew.B_Cu, zone_points, clearance=0.3)
    # Zone filling is deferred to KiCad proper; see the note on the main board.
    return board


def project_json(name: str) -> str:
    return json.dumps(
        {
            "board": {},
            "boards": [],
            "cvpcb": {},
            "erc": {},
            "libraries": {},
            "meta": {"filename": f"{name}.kicad_pro", "version": 1},
            "net_settings": {"classes": [], "meta": {"version": 3}},
            "pcbnew": {},
            "schematic": {},
            "text_variables": {"DESIGN_STATUS": "ENGINEERING_DRAFT"},
        },
        indent=2,
        sort_keys=True,
    ) + "\n"


def write_project_file(directory: Path, name: str) -> None:
    (directory / f"{name}.kicad_pro").write_text(project_json(name), encoding="utf-8")


def stable_uuid(name: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"https://github.com/hdh7485/agent-deck/{name}"))


def sch_quote(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def sch_text(value: str, x: float, y: float, size: float, key: str, *, bold: bool = False) -> str:
    bold_line = "\n\t\t\t\t(bold yes)" if bold else ""
    return f'''\t(text "{sch_quote(value)}"
\t\t(exclude_from_sim no)
\t\t(at {x:.3f} {y:.3f} 0)
\t\t(effects
\t\t\t(font
\t\t\t\t(size {size:.3f} {size:.3f}){bold_line}
\t\t\t)
\t\t\t(justify left top)
\t\t)
\t\t(uuid "{stable_uuid(key)}")
\t)'''


def sch_polyline(points: list[tuple[float, float]], key: str, width: float = 0.35) -> str:
    point_text = " ".join(f"(xy {x:.3f} {y:.3f})" for x, y in points)
    return f'''\t(polyline
\t\t(pts {point_text})
\t\t(stroke (width {width:.3f}) (type solid))
\t\t(uuid "{stable_uuid(key)}")
\t)'''


def sch_box(x1: float, y1: float, x2: float, y2: float, key: str) -> str:
    return sch_polyline([(x1, y1), (x2, y1), (x2, y2), (x1, y2), (x1, y1)], key, 0.5)


def write_block_schematic(
    path: Path,
    title: str,
    boxes: list[tuple[float, float, float, float, str]],
    lines: list[list[tuple[float, float]]],
    notes: list[str],
) -> None:
    doc_uuid = stable_uuid(str(path.relative_to(ROOT)))
    items: list[str] = [sch_text(title, 18, 12, 2.4, f"{path}-title", bold=True)]
    items.append(sch_text("ENGINEERING BLOCK SCHEMATIC • PCB NET ASSIGNMENTS ARE AUTHORITATIVE", 18, 17, 1.0, f"{path}-status"))
    for index, (x1, y1, x2, y2, label) in enumerate(boxes):
        items.append(sch_box(x1, y1, x2, y2, f"{path}-box-{index}"))
        items.append(sch_text(label, x1 + 2.5, y1 + 2.5, 1.15, f"{path}-label-{index}", bold=True))
    for index, line in enumerate(lines):
        items.append(sch_polyline(line, f"{path}-line-{index}", 0.45))
    for index, note in enumerate(notes):
        items.append(sch_text(f"• {note}", 18, 157 + index * 5, 0.95, f"{path}-note-{index}"))
    document = f'''(kicad_sch
\t(version 20231120)
\t(generator "eeschema")
\t(generator_version "8.0")
\t(uuid "{doc_uuid}")
\t(paper "A4")
\t(lib_symbols)
{chr(10).join(items)}
\t(sheet_instances
\t\t(path "/" (page "1"))
\t)
)
'''
    path.write_text(document, encoding="utf-8")


def write_schematics() -> None:
    main_path = OUT_ROOT / "input-main" / "input-main.kicad_sch"
    write_block_schematic(
        main_path,
        "AGENT DECK V1 — COMMON INPUT PCB",
        [
            (18, 28, 65, 57, "J1 COMMON ADAPTER\n3V3 / VBUS / GND\nI2C / INT / RGB / ENC"),
            (88, 24, 140, 63, "U1 MCP23017 @ 3V3\nGPA0..3  ROW0..3\nGPA4..7  COL0..3\nGPB0..4  NAV\nGPB5      TOUCH_OUT"),
            (164, 24, 216, 50, "SW1..SW13 + D1..D13\nMX + 1N4148W\n4 × 4 MATRIX / 13 USED"),
            (164, 58, 216, 82, "NAV1 5-WAY DIGITAL\nUP / DOWN / LEFT / RIGHT\nCENTER + COMMON"),
            (88, 75, 140, 106, "U2 AT42QT1010-TSHR\n14 mm ROUND ELECTRODE\n1k Rs + 10nF Cs\nDIGITAL OUT → U1"),
            (18, 73, 65, 99, "ENC1 EC11\nA / B / CLICK\nDIRECT MCU GPIO\nNO I2C EDGE PATH"),
            (18, 116, 65, 146, "U3 TPS2553DBVR\nVBUS → LED_5V\n232k ILIM ≈ 117mA typ.\nDEFAULT-OFF EN PULLDOWN"),
            (88, 116, 140, 146, "U4 SN74AHCT1G125\nQ1 OE INVERTER\n3V3 DATA → 5V DATA\n330R FIRST-LED SERIES"),
            (164, 112, 216, 147, "LED1..LED6 SK6812 MINI-E\nADDRESSABLE DATA CHAIN\n100nF AT EACH LED\n10uF + 470uF BULK"),
        ],
        [
            [(65, 40), (88, 40)],
            [(140, 36), (164, 36)],
            [(140, 69), (152, 69), (152, 69), (164, 69)],
            [(114, 63), (114, 75)],
            [(41, 57), (41, 73)],
            [(41, 57), (41, 116)],
            [(65, 131), (88, 131)],
            [(140, 131), (164, 131)],
            [(65, 43), (76, 43), (76, 126), (88, 126)],
        ],
        [
            "No OLED/LCD. All user inputs and the touch electrode are fixed to this PCB.",
            "The six reverse-mount LED cutouts require a reviewed local DRC waiver or revised land pattern.",
            "Long traces are intentionally unrouted until switch, navigation, connector, and plate dimensions are locked.",
            "This is an independent functional design; no unpublished OpenAI Micro internals are asserted.",
        ],
    )

    for name, title, board_note in (
        ("xiao-esp32s3-plus", "XIAO ESP32-S3 PLUS ADAPTER", "ESP32-S3 board-specific boot/JTAG/battery behavior remains adapter-local."),
        ("xiao-nrf52840-plus", "XIAO nRF52840 PLUS ADAPTER", "nRF52840 NFC/SWD/battery behavior remains adapter-local."),
    ):
        path = OUT_ROOT / "adapters" / name / f"{name}.kicad_sch"
        write_block_schematic(
            path,
            f"AGENT DECK V1 — {title}",
            [
                (18, 30, 72, 100, "J1 COMMON 2 × 10\n1  3V3     2  GND\n3  VBUS    4  GND\n5  SDA     6  SCL\n7  IOX_INT 8  RGB_DATA\n9  RGB_EN 10  ENC_A\n11 ENC_B  12  ENC_SW\n13 TX     14  RX\n15/16 SPARE\n17..20 GND"),
                (100, 26, 176, 108, "MOD1 XIAO PLUS\nOFFICIAL PHYSICAL PAD PATTERN\n\nD0  RGB_DATA\nD1  IOX_INT\nD3  RGB_PWR_EN\nD4  I2C_SDA\nD5  I2C_SCL\nD6/D7 DEBUG UART\nD8/D9/D10 ENCODER\n3V3 / VBUS / GND\nD16 BAT SENSE — RESERVED"),
                (194, 30, 228, 60, "ONBOARD USB-C\nEXPOSED IN V1\nNO SECOND USB-C"),
                (194, 75, 228, 105, "TP1 D16\nBAT SENSE ONLY\nNOT A GENERIC GPIO"),
            ],
            [
                [(72, 64), (100, 64)],
                [(176, 44), (194, 44)],
                [(176, 90), (194, 90)],
            ],
            [
                board_note,
                "The common connector uses only the conservative officially-verified D-pin subset.",
                "USB-C, charger, antenna keep-out, and service pads follow the exact purchased board revision.",
                "Adapter routing remains unrouted until connector mating height and enclosure USB datum are locked.",
            ],
        )


def save_board(board: pcbnew.BOARD, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not pcbnew.SaveBoard(str(path), board):
        raise RuntimeError(f"Failed to save {path}")


def main() -> None:
    ensure_dirs()
    boards = [
        (main_board(), OUT_ROOT / "input-main" / "input-main.kicad_pcb"),
        (
            xiao_adapter_board("xiao-esp32s3-plus", "XIAO ESP32-S3 PLUS"),
            OUT_ROOT / "adapters" / "xiao-esp32s3-plus" / "xiao-esp32s3-plus.kicad_pcb",
        ),
        (
            xiao_adapter_board("xiao-nrf52840-plus", "XIAO nRF52840 PLUS"),
            OUT_ROOT / "adapters" / "xiao-nrf52840-plus" / "xiao-nrf52840-plus.kicad_pcb",
        ),
    ]
    for board, path in boards:
        save_board(board, path)
        print(f"generated {path.relative_to(ROOT)}")
    write_project_file(OUT_ROOT / "input-main", "input-main")
    write_project_file(OUT_ROOT / "adapters" / "xiao-esp32s3-plus", "xiao-esp32s3-plus")
    write_project_file(OUT_ROOT / "adapters" / "xiao-nrf52840-plus", "xiao-nrf52840-plus")
    write_schematics()
    print("generated KiCad block schematics")


if __name__ == "__main__":
    main()
