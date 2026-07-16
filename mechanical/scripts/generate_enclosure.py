#!/usr/bin/env python3
"""Generate the Agent Deck V1 enclosure fit-check with Blender.

Run with Blender, not the system Python:

    blender --background --factory-startup --python mechanical/scripts/generate_enclosure.py

Coordinates are millimetres and share the common input PCB's lower-left board
corner as X=0, Y=0.  The STL files are unitless but intentionally use
millimetre-sized coordinates for normal slicer import.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[2]
EXPORT_DIR = ROOT / "mechanical" / "exports" / "v1-fit-check"
IMAGE_DIR = ROOT / "docs" / "images" / "mechanical"
ARTIFACT_DIR = ROOT / "artifacts" / "mechanical"

# PCB-derived coordinates from hardware/kicad/scripts/generate_design.py.
PCB_W = 100.0
PCB_D = 100.0
PCB_THICKNESS = 1.6
MOUNT_HOLES = [(5.0, 5.0), (95.0, 5.0), (5.0, 95.0), (95.0, 95.0)]
KEY_POSITIONS = [
    (42.0, 79.0),
    (61.0, 79.0),
    (23.0, 60.0),
    (42.0, 60.0),
    (61.0, 60.0),
    (80.0, 60.0),
    (23.0, 41.0),
    (42.0, 41.0),
    (61.0, 41.0),
    (80.0, 41.0),
    (51.5, 22.0),
    (80.0, 22.0),
]
ENCODER_POS = (19.0, 79.0)
NAV_POS = (80.0, 79.0)
TOUCH_POS = (23.0, 22.0)

# Fit-check enclosure parameters.  Candidate envelopes are manufacturer-backed
# where possible, but samples and formal supply drawings remain the release
# gate for USB, battery swelling/leads, navigation and stabilizer details.
CLEARANCE = 1.5
WALL = 2.4
BASE_T = 2.4
BATTERY_ADHESIVE_T = 0.4
BATTERY_SIZE = (34.5, 45.0, 6.0)
BATTERY_CENTER = (48.0, 78.0)
BATTERY_Z = BASE_T + BATTERY_ADHESIVE_T
BATTERY_SWELLING_CLEARANCE = 1.5
ADAPTER_PCB_SIZE = (81.0, 43.0)
ADAPTER_PCB_CENTER = (60.0, 79.0)
ADAPTER_PCB_Z = BATTERY_Z + BATTERY_SIZE[2] + BATTERY_SWELLING_CLEARANCE
ADAPTER_PCB_THICKNESS = 1.6
ADAPTER_HOLES = [(23.5, 61.5), (96.5, 61.5), (70.0, 89.0), (88.0, 89.0)]
COMMON_CONNECTOR_STACK = 7.47
MAIN_PCB_Z = ADAPTER_PCB_Z + ADAPTER_PCB_THICKNESS + COMMON_CONNECTOR_STACK
CONTROL_BODY_CLEARANCE = 7.2
PLATE_LEDGE_H = 2.0
BOTTOM_H = MAIN_PCB_Z + PCB_THICKNESS + CONTROL_BODY_CLEARANCE - PLATE_LEDGE_H
PCB_STANDOFF = MAIN_PCB_Z
OUTER_W = PCB_W + 2.0 * (CLEARANCE + WALL)
OUTER_D = PCB_D + 2.0 * (CLEARANCE + WALL)
CASE_CX = PCB_W / 2.0
CASE_CY = PCB_D / 2.0
CASE_RADIUS = 5.0

PLATE_W = PCB_W + 0.8
PLATE_D = PCB_D + 0.8
PLATE_T = 1.5
PLATE_RADIUS = 3.2
BEZEL_H = 7.0
MX_CUTOUT = 14.2
STABILIZER_CUTOUT = (6.8, 14.2)
STABILIZER_CENTERS = [(KEY_POSITIONS[10][0] - 11.9, KEY_POSITIONS[10][1]), (KEY_POSITIONS[10][0] + 11.9, KEY_POSITIONS[10][1])]
KEYCAP_1U = (17.2, 17.2)
PTT_KEYCAP_2U = (36.2, 17.2)
ENCODER_HOLE_D = 8.4
NAV_HOLE_D = 12.0
NAV_BODY_D = 11.0
NAV_CAP_D = 14.0
NAV_CAP_H = 4.0
TOUCH_RECESS_D = 18.0
TOUCH_MEMBRANE = 0.8
FASTENER_D = 3.4
BOSS_D = 7.6
ADAPTER_BOSS_D = 7.0
TOP_BOSS_D = 10.0
USB_CENTER_Y = 76.0
USB_SLOT_W = 12.5
USB_SLOT_H = 8.0
USB_SLOT_Z0 = ADAPTER_PCB_Z - 0.8


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for datablocks in (bpy.data.meshes, bpy.data.curves, bpy.data.materials, bpy.data.cameras, bpy.data.lights):
        for block in list(datablocks):
            if block.users == 0:
                datablocks.remove(block)


def rounded_prism(
    name: str,
    width: float,
    depth: float,
    height: float,
    *,
    center: tuple[float, float] = (0.0, 0.0),
    z0: float = 0.0,
    radius: float = 0.0,
    segments: int = 8,
) -> bpy.types.Object:
    """Create a flat-bottomed rounded rectangular prism."""

    radius = max(0.0, min(radius, width / 2.0, depth / 2.0))
    if radius == 0.0:
        outline = [
            (width / 2.0, depth / 2.0),
            (-width / 2.0, depth / 2.0),
            (-width / 2.0, -depth / 2.0),
            (width / 2.0, -depth / 2.0),
        ]
    else:
        outline: list[tuple[float, float]] = []
        corners = [
            (width / 2.0 - radius, depth / 2.0 - radius, 0.0),
            (-width / 2.0 + radius, depth / 2.0 - radius, 90.0),
            (-width / 2.0 + radius, -depth / 2.0 + radius, 180.0),
            (width / 2.0 - radius, -depth / 2.0 + radius, 270.0),
        ]
        for cx, cy, start_angle in corners:
            for step in range(segments + 1):
                angle = math.radians(start_angle + step * 90.0 / segments)
                outline.append((cx + radius * math.cos(angle), cy + radius * math.sin(angle)))

    cx, cy = center
    bottom = [(cx + x, cy + y, z0) for x, y in outline]
    top = [(cx + x, cy + y, z0 + height) for x, y in outline]
    vertices = bottom + top
    count = len(outline)
    faces: list[tuple[int, ...]] = [tuple(reversed(range(count))), tuple(range(count, count * 2))]
    for index in range(count):
        next_index = (index + 1) % count
        faces.append((index, next_index, next_index + count, index + count))

    mesh = bpy.data.meshes.new(f"{name}_mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return obj


def cube(name: str, size: tuple[float, float, float], location: tuple[float, float, float]) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cube_add(location=location)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return obj


def cylinder(
    name: str,
    diameter: float,
    height: float,
    *,
    center: tuple[float, float],
    z0: float,
    vertices: int = 64,
) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=vertices,
        radius=diameter / 2.0,
        depth=height,
        location=(center[0], center[1], z0 + height / 2.0),
    )
    obj = bpy.context.object
    obj.name = name
    return obj


def apply_boolean(target: bpy.types.Object, tool: bpy.types.Object, operation: str) -> None:
    bpy.context.view_layer.objects.active = target
    target.select_set(True)
    tool.select_set(False)
    modifier = target.modifiers.new(name=f"{operation}_{tool.name}", type="BOOLEAN")
    modifier.operation = operation
    modifier.solver = "EXACT"
    modifier.object = tool
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    bpy.data.objects.remove(tool, do_unlink=True)


def add_bevel(obj: bpy.types.Object, width: float = 0.7, segments: int = 3) -> None:
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    modifier = obj.modifiers.new(name="print_edge_softening", type="BEVEL")
    modifier.width = width
    modifier.segments = segments
    modifier.limit_method = "ANGLE"
    bpy.ops.object.modifier_apply(modifier=modifier.name)


def build_bottom() -> bpy.types.Object:
    bottom = rounded_prism(
        "bottom_tray",
        OUTER_W,
        OUTER_D,
        BOTTOM_H,
        center=(CASE_CX, CASE_CY),
        radius=CASE_RADIUS,
    )
    cavity = rounded_prism(
        "bottom_cavity",
        PCB_W + 2.0 * CLEARANCE,
        PCB_D + 2.0 * CLEARANCE,
        BOTTOM_H - BASE_T + 1.0,
        center=(CASE_CX, CASE_CY),
        z0=BASE_T,
        radius=max(1.0, CASE_RADIUS - WALL),
    )
    apply_boolean(bottom, cavity, "DIFFERENCE")

    boss_height = PCB_STANDOFF - BASE_T
    for index, position in enumerate(MOUNT_HOLES, start=1):
        boss = cylinder(
            f"bottom_boss_{index}",
            BOSS_D,
            boss_height + 0.4,
            center=position,
            z0=BASE_T - 0.2,
        )
        apply_boolean(bottom, boss, "UNION")
        hole = cylinder(
            f"bottom_fastener_{index}",
            FASTENER_D,
            PCB_STANDOFF + 2.0,
            center=position,
            z0=-1.0,
        )
        apply_boolean(bottom, hole, "DIFFERENCE")

    for index, position in enumerate(ADAPTER_HOLES, start=1):
        boss = cube(
            f"adapter_boss_{index}",
            (ADAPTER_BOSS_D, ADAPTER_BOSS_D, ADAPTER_PCB_Z + 0.4),
            (position[0], position[1], (ADAPTER_PCB_Z + 0.4) / 2.0),
        )
        apply_boolean(bottom, boss, "UNION")
        hole = cylinder(
            f"adapter_fastener_{index}",
            FASTENER_D,
            ADAPTER_PCB_Z + 1.0,
            center=position,
            z0=-0.5,
        )
        apply_boolean(bottom, hole, "DIFFERENCE")

    service_slot = cube(
        "xiao_usb_c_slot",
        (WALL * 4.0, USB_SLOT_W, USB_SLOT_H),
        (
            CASE_CX + OUTER_W / 2.0 - WALL / 2.0,
            USB_CENTER_Y,
            USB_SLOT_Z0 + USB_SLOT_H / 2.0,
        ),
    )
    apply_boolean(bottom, service_slot, "DIFFERENCE")
    return bottom


def build_bezel() -> bpy.types.Object:
    bezel = rounded_prism(
        "top_bezel",
        OUTER_W,
        OUTER_D,
        BEZEL_H,
        center=(CASE_CX, CASE_CY),
        radius=CASE_RADIUS,
    )
    opening = rounded_prism(
        "bezel_opening",
        PLATE_W + 0.6,
        PLATE_D + 0.6,
        BEZEL_H + 2.0,
        center=(CASE_CX, CASE_CY),
        z0=-1.0,
        radius=PLATE_RADIUS + 0.3,
    )
    apply_boolean(bezel, opening, "DIFFERENCE")

    ledge = rounded_prism(
        "plate_ledge_outer",
        PLATE_W + 3.0,
        PLATE_D + 3.0,
        PLATE_LEDGE_H,
        center=(CASE_CX, CASE_CY),
        radius=PLATE_RADIUS + 1.0,
    )
    ledge_opening = rounded_prism(
        "plate_ledge_opening",
        PLATE_W - 3.2,
        PLATE_D - 3.2,
        PLATE_LEDGE_H + 2.0,
        center=(CASE_CX, CASE_CY),
        z0=-1.0,
        radius=max(1.0, PLATE_RADIUS - 1.0),
    )
    apply_boolean(ledge, ledge_opening, "DIFFERENCE")
    apply_boolean(bezel, ledge, "UNION")

    for index, position in enumerate(MOUNT_HOLES, start=1):
        boss = cylinder(f"top_boss_{index}", TOP_BOSS_D, BEZEL_H, center=position, z0=0.0)
        apply_boolean(bezel, boss, "UNION")
        hole = cylinder(
            f"top_fastener_{index}",
            FASTENER_D,
            BEZEL_H + 2.0,
            center=position,
            z0=-1.0,
        )
        apply_boolean(bezel, hole, "DIFFERENCE")
    return bezel


def build_plate() -> bpy.types.Object:
    plate = rounded_prism(
        "control_plate",
        PLATE_W,
        PLATE_D,
        PLATE_T,
        center=(CASE_CX, CASE_CY),
        radius=PLATE_RADIUS,
    )
    for index, (x, y) in enumerate(KEY_POSITIONS, start=1):
        cutout = cube(f"mx_cutout_{index}", (MX_CUTOUT, MX_CUTOUT, PLATE_T + 2.0), (x, y, PLATE_T / 2.0))
        apply_boolean(plate, cutout, "DIFFERENCE")

    for index, position in enumerate(STABILIZER_CENTERS, start=1):
        cutout = cube(
            f"ptt_stabilizer_cutout_{index}",
            (STABILIZER_CUTOUT[0], STABILIZER_CUTOUT[1], PLATE_T + 2.0),
            (position[0], position[1], PLATE_T / 2.0),
        )
        apply_boolean(plate, cutout, "DIFFERENCE")

    for name, position, diameter in (
        ("encoder_shaft", ENCODER_POS, ENCODER_HOLE_D),
        ("navigation_cap", NAV_POS, NAV_HOLE_D),
    ):
        cutout = cylinder(name, diameter, PLATE_T + 2.0, center=position, z0=-1.0)
        apply_boolean(plate, cutout, "DIFFERENCE")

    recess_depth = PLATE_T - TOUCH_MEMBRANE
    touch_recess = cylinder(
        "touch_recess",
        TOUCH_RECESS_D,
        recess_depth + 0.2,
        center=TOUCH_POS,
        z0=TOUCH_MEMBRANE,
    )
    apply_boolean(plate, touch_recess, "DIFFERENCE")

    for index, position in enumerate(MOUNT_HOLES, start=1):
        boss_clearance = cylinder(
            f"plate_boss_clearance_{index}",
            TOP_BOSS_D + 0.4,
            PLATE_T + 2.0,
            center=position,
            z0=-1.0,
        )
        apply_boolean(plate, boss_clearance, "DIFFERENCE")
    return plate


def mesh_stats(obj: bpy.types.Object) -> dict[str, float | int | bool]:
    mesh = obj.data
    mesh.validate(verbose=False)
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.normal_update()
    non_manifold = sum(1 for edge in bm.edges if not edge.is_manifold)
    volume = abs(bm.calc_volume(signed=True))
    stats: dict[str, float | int | bool] = {
        "vertices": len(bm.verts),
        "faces": len(bm.faces),
        "non_manifold_edges": non_manifold,
        "volume_mm3": round(volume, 2),
        "manifold": non_manifold == 0,
    }
    bm.free()
    if non_manifold:
        raise RuntimeError(f"{obj.name} has {non_manifold} non-manifold edges")
    if volume <= 0.0:
        raise RuntimeError(f"{obj.name} has no closed volume")
    return stats


def export_stl(obj: bpy.types.Object, filename: str) -> None:
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.wm.stl_export(
        filepath=str(EXPORT_DIR / filename),
        check_existing=False,
        ascii_format=False,
        export_selected_objects=True,
        global_scale=1.0,
        use_scene_unit=False,
        apply_modifiers=True,
        forward_axis="Y",
        up_axis="Z",
    )


def make_material(
    name: str,
    color: tuple[float, float, float, float],
    metallic: float = 0.0,
    roughness: float = 0.45,
    transmission: float = 0.0,
) -> bpy.types.Material:
    material = bpy.data.materials.get(name) or bpy.data.materials.new(name=name)
    material.diffuse_color = color
    material.use_nodes = True
    shader = material.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = color
    shader.inputs["Metallic"].default_value = metallic
    shader.inputs["Roughness"].default_value = roughness
    transmission_input = shader.inputs.get("Transmission Weight") or shader.inputs.get("Transmission")
    if transmission_input is not None:
        transmission_input.default_value = transmission
    if transmission > 0.0 and shader.inputs.get("IOR") is not None:
        shader.inputs["IOR"].default_value = 1.46
    return material


def assign_material(obj: bpy.types.Object, material: bpy.types.Material) -> None:
    obj.data.materials.clear()
    obj.data.materials.append(material)


def add_render_proxies(plate_top_z: float) -> dict[str, list[bpy.types.Object]]:
    main_pcb_material = make_material("pcb_green", (0.035, 0.19, 0.12, 1.0), metallic=0.05, roughness=0.35)
    adapter_pcb_material = make_material("adapter_blue", (0.025, 0.12, 0.24, 1.0), metallic=0.08, roughness=0.32)
    component_material = make_material("component_black", (0.025, 0.028, 0.034, 1.0), metallic=0.1, roughness=0.34)
    metal_material = make_material("connector_metal", (0.48, 0.52, 0.58, 1.0), metallic=0.82, roughness=0.22)
    envelope_material = make_material(
        "fit_envelope",
        (0.12, 0.42, 0.85, 0.34),
        metallic=0.0,
        roughness=0.25,
        transmission=0.62,
    )

    battery = rounded_prism(
        "battery_lp603443ju_envelope",
        BATTERY_SIZE[0],
        BATTERY_SIZE[1],
        BATTERY_SIZE[2],
        center=BATTERY_CENTER,
        z0=BATTERY_Z,
        radius=2.0,
    )
    assign_material(battery, make_material("battery_pouch", (0.30, 0.32, 0.35, 1.0), metallic=0.65, roughness=0.24))

    adapter_pcb = rounded_prism(
        "mcu_adapter_pcb",
        ADAPTER_PCB_SIZE[0],
        ADAPTER_PCB_SIZE[1],
        ADAPTER_PCB_THICKNESS,
        center=ADAPTER_PCB_CENTER,
        z0=ADAPTER_PCB_Z,
        radius=2.5,
    )
    assign_material(adapter_pcb, adapter_pcb_material)

    connector_stack = cube(
        "hle_tsm_7p47_stack",
        (25.9, 5.1, COMMON_CONNECTOR_STACK),
        (33.0, 94.0, ADAPTER_PCB_Z + ADAPTER_PCB_THICKNESS + COMMON_CONNECTOR_STACK / 2.0),
    )
    add_bevel(connector_stack, width=0.35, segments=3)
    assign_material(connector_stack, component_material)

    xiao_pcb = rounded_prism(
        "xiao_plus_module",
        21.0,
        17.8,
        1.6,
        center=(90.0, USB_CENTER_Y),
        z0=ADAPTER_PCB_Z + ADAPTER_PCB_THICKNESS,
        radius=1.0,
    )
    assign_material(xiao_pcb, main_pcb_material)

    usb_shell = cube(
        "xiao_usb_c_shell_envelope",
        (7.0, 9.2, 3.2),
        (101.8, USB_CENTER_Y, ADAPTER_PCB_Z + ADAPTER_PCB_THICKNESS + 2.0),
    )
    add_bevel(usb_shell, width=0.35, segments=3)
    assign_material(usb_shell, metal_material)

    usb_cable = cube(
        "usb_c_plug_and_bend_envelope",
        (12.0, 12.0, 7.0),
        (107.0, USB_CENTER_Y, ADAPTER_PCB_Z + ADAPTER_PCB_THICKNESS + 2.4),
    )
    add_bevel(usb_cable, width=0.8, segments=4)
    assign_material(usb_cable, envelope_material)

    rf_keepout = cube(
        "xiao_rf_keepout_envelope",
        (3.0, 22.0, 8.5),
        (80.0, 76.0, ADAPTER_PCB_Z + ADAPTER_PCB_THICKNESS + 4.25),
    )
    assign_material(rf_keepout, make_material("rf_keepout", (0.75, 0.08, 0.04, 0.3), roughness=0.3, transmission=0.7))

    main_pcb = rounded_prism(
        "input_main_pcb",
        PCB_W,
        PCB_D,
        PCB_THICKNESS,
        center=(CASE_CX, CASE_CY),
        z0=MAIN_PCB_Z,
        radius=4.0,
    )
    assign_material(main_pcb, main_pcb_material)

    main_components: list[bpy.types.Object] = []
    for index, (x, y) in enumerate(KEY_POSITIONS, start=1):
        socket = cube(
            f"kailh_socket_{index}",
            (14.65, 5.99, 1.95),
            (x, y, MAIN_PCB_Z - 1.95 / 2.0),
        )
        add_bevel(socket, width=0.25, segments=2)
        assign_material(socket, component_material)
        main_components.append(socket)

        switch_body = cube(
            f"mx2a_switch_body_{index}",
            (14.0, 14.0, 8.0),
            (x, y, MAIN_PCB_Z + PCB_THICKNESS + 4.0),
        )
        add_bevel(switch_body, width=0.45, segments=3)
        assign_material(switch_body, make_material("switch_smoke", (0.08, 0.09, 0.11, 0.62), roughness=0.25, transmission=0.28))
        main_components.append(switch_body)

    c30 = cube(
        "c30_low_profile_proxy",
        (7.3, 4.3, 2.8),
        (60.0, 92.0, MAIN_PCB_Z + PCB_THICKNESS + 1.4),
    )
    add_bevel(c30, width=0.35, segments=3)
    assign_material(c30, make_material("polymer_cap", (0.82, 0.43, 0.055, 1.0), metallic=0.18, roughness=0.28))
    main_components.append(c30)

    u1 = cube(
        "mcp23017_backside_envelope",
        (10.3, 7.5, 2.65),
        (78.0, 7.0, MAIN_PCB_Z - 2.65 / 2.0),
    )
    add_bevel(u1, width=0.3, segments=2)
    assign_material(u1, component_material)
    main_components.append(u1)

    for index, position in enumerate(STABILIZER_CENTERS, start=1):
        housing = cube(
            f"gateron_2u_stabilizer_housing_{index}",
            (6.8, 14.2, 3.2),
            (position[0], position[1], MAIN_PCB_Z - 1.6),
        )
        add_bevel(housing, width=0.35, segments=3)
        assign_material(housing, component_material)
        main_components.append(housing)

        stem = cylinder(
            f"gateron_2u_stabilizer_stem_{index}",
            4.2,
            CONTROL_BODY_CLEARANCE + PCB_THICKNESS,
            center=position,
            z0=MAIN_PCB_Z,
        )
        assign_material(stem, component_material)
        main_components.append(stem)

    encoder_body = cube(
        "ec11e15244g1_body",
        (11.7, 12.0, 6.6),
        (ENCODER_POS[0], ENCODER_POS[1], MAIN_PCB_Z + PCB_THICKNESS + 3.3),
    )
    add_bevel(encoder_body, width=0.45, segments=3)
    assign_material(encoder_body, metal_material)
    main_components.append(encoder_body)

    nav_body = cube(
        "rkjxm1015004_body",
        (11.0, 11.0, 6.6),
        (NAV_POS[0], NAV_POS[1], MAIN_PCB_Z + PCB_THICKNESS + 3.3),
    )
    add_bevel(nav_body, width=0.45, segments=3)
    assign_material(nav_body, component_material)
    main_components.append(nav_body)

    keycap_material = make_material(
        "key_smoke_translucent",
        (0.012, 0.016, 0.022, 1.0),
        metallic=0.04,
        roughness=0.18,
        transmission=0.38,
    )
    keycaps: list[bpy.types.Object] = []
    for index, (x, y) in enumerate(KEY_POSITIONS):
        keycap_width, keycap_depth = PTT_KEYCAP_2U if index == 10 else KEYCAP_1U
        keycap = cube(
            f"keycap_{index + 1}",
            (keycap_width, keycap_depth, 6.8),
            (x, y, plate_top_z + 4.0),
        )
        add_bevel(keycap, width=1.2, segments=5)
        assign_material(keycap, keycap_material)
        keycaps.append(keycap)

    knob = cylinder("encoder_knob", 16.0, 13.0, center=ENCODER_POS, z0=plate_top_z)
    add_bevel(knob, width=0.8, segments=4)
    assign_material(knob, make_material("knob", (0.055, 0.06, 0.07, 1.0), metallic=0.6, roughness=0.24))

    nav = cylinder("navigation_cap", NAV_CAP_D, NAV_CAP_H, center=NAV_POS, z0=plate_top_z)
    add_bevel(nav, width=0.9, segments=5)
    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=64,
        ring_count=32,
        radius=10.0,
        location=(NAV_POS[0], NAV_POS[1], plate_top_z + 13.0),
    )
    dimple = bpy.context.object
    dimple.name = "navigation_cap_dimple"
    apply_boolean(nav, dimple, "DIFFERENCE")
    assign_material(nav, make_material("nav_cap", (0.13, 0.14, 0.16, 1.0), metallic=0.2, roughness=0.28))

    touch = cylinder("touch_surface", TOUCH_RECESS_D - 1.0, 0.45, center=TOUCH_POS, z0=plate_top_z + 0.05)
    assign_material(touch, make_material("touch_surface", (0.07, 0.08, 0.09, 1.0), metallic=0.35, roughness=0.2))

    return {
        "battery": [battery],
        "adapter": [adapter_pcb, connector_stack, xiao_pcb, usb_shell],
        "fit_envelopes": [usb_cable, rf_keepout],
        "main": [main_pcb] + main_components,
        "controls": keycaps + [knob, nav, touch],
    }


def point_camera(camera: bpy.types.Object, target: tuple[float, float, float]) -> None:
    direction = Vector(target) - camera.location
    camera.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def setup_render() -> bpy.types.Object:
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1800
    scene.render.resolution_y = 1200
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.render.image_settings.color_mode = "RGBA"
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.view_settings.exposure = 1.0
    scene.world.color = (0.025, 0.028, 0.035)

    world = scene.world
    world.use_nodes = True
    background = world.node_tree.nodes.get("Background")
    background.inputs["Color"].default_value = (0.018, 0.022, 0.03, 1.0)
    background.inputs["Strength"].default_value = 0.65

    bpy.ops.object.camera_add(location=(180.0, -125.0, 132.0))
    camera = bpy.context.object
    camera.data.lens = 58.0
    point_camera(camera, (CASE_CX, CASE_CY, 8.0))
    scene.camera = camera

    for name, location, energy, size, color in (
        ("key_light", (25.0, -75.0, 180.0), 85000.0, 95.0, (0.92, 0.96, 1.0)),
        ("fill_light", (190.0, 95.0, 95.0), 52000.0, 80.0, (0.55, 0.72, 1.0)),
        ("rim_light", (-65.0, 130.0, 115.0), 68000.0, 65.0, (1.0, 0.42, 0.18)),
    ):
        light_data = bpy.data.lights.new(name=name, type="AREA")
        light_data.energy = energy
        light_data.shape = "DISK"
        light_data.size = size
        light_data.color = color
        light = bpy.data.objects.new(name, light_data)
        bpy.context.collection.objects.link(light)
        light.location = location
        point_camera(light, (CASE_CX, CASE_CY, 8.0))

    floor = rounded_prism("studio_floor", 420.0, 360.0, 1.0, center=(CASE_CX, CASE_CY), z0=-1.4, radius=18.0)
    assign_material(floor, make_material("studio_floor", (0.045, 0.052, 0.066, 1.0), metallic=0.1, roughness=0.42))
    return camera


def render(path: Path) -> None:
    bpy.context.scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)


def main() -> None:
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    clear_scene()

    assert math.isclose(
        MAIN_PCB_Z,
        ADAPTER_PCB_Z + ADAPTER_PCB_THICKNESS + COMMON_CONNECTOR_STACK,
        abs_tol=1e-6,
    )
    assert ADAPTER_PCB_Z - (BATTERY_Z + BATTERY_SIZE[2]) >= BATTERY_SWELLING_CLEARANCE
    assert (
        BOTTOM_H + PLATE_LEDGE_H - (MAIN_PCB_Z + PCB_THICKNESS)
        >= CONTROL_BODY_CLEARANCE - 1e-6
    )

    bottom = build_bottom()
    bezel = build_bezel()
    plate = build_plate()
    stats = {obj.name: mesh_stats(obj) for obj in (bottom, bezel, plate)}

    export_stl(bottom, "agent-deck-v1-bottom.stl")
    export_stl(bezel, "agent-deck-v1-top-bezel.stl")
    export_stl(plate, "agent-deck-v1-mx-plate.stl")

    dimensions = {
        "status": "V1_FIT_CHECK_NOT_FABRICATION_RELEASE",
        "units": "mm",
        "pcb": {"width": PCB_W, "depth": PCB_D, "thickness": PCB_THICKNESS},
        "case": {
            "outer_width": OUTER_W,
            "outer_depth": OUTER_D,
            "assembled_body_height_without_controls": BOTTOM_H + BEZEL_H,
            "wall": WALL,
            "base": BASE_T,
            "main_pcb_bottom_z": MAIN_PCB_Z,
            "adapter_pcb_bottom_z": ADAPTER_PCB_Z,
        },
        "internal_stack": {
            "battery_candidate": "Jauch LP603443JU protected 1S LiPo",
            "battery_envelope": BATTERY_SIZE,
            "battery_bottom_z": BATTERY_Z,
            "battery_top_z": BATTERY_Z + BATTERY_SIZE[2],
            "battery_to_adapter_clearance": round(
                ADAPTER_PCB_Z - (BATTERY_Z + BATTERY_SIZE[2]), 2
            ),
            "adapter_pcb_size": ADAPTER_PCB_SIZE,
            "adapter_pcb_thickness": ADAPTER_PCB_THICKNESS,
            "common_connector_candidates": [
                "Samtec HLE-110-02-G-DV-A",
                "Samtec TSM-110-04-L-DV-A",
            ],
            "common_connector_stack_height": COMMON_CONNECTOR_STACK,
            "main_pcb_bottom_z": MAIN_PCB_Z,
            "main_pcb_top_z": MAIN_PCB_Z + PCB_THICKNESS,
            "main_pcb_to_plate_bottom": CONTROL_BODY_CLEARANCE,
            "xiao_board_envelope": [21.0, 17.8, 1.6],
            "xiao_center": [90.0, USB_CENTER_Y],
            "rf_keepout_envelope": [3.0, 22.0, 8.5],
        },
        "plate": {
            "width": PLATE_W,
            "depth": PLATE_D,
            "thickness": PLATE_T,
            "mx_cutout": MX_CUTOUT,
            "touch_membrane": TOUCH_MEMBRANE,
            "hotswap_socket_candidate": "Kailh CPG151101S11-16",
            "hotswap_socket_body_below_pcb": 1.85,
            "hotswap_socket_floor_clearance": round(PCB_STANDOFF - 1.85 - BASE_T, 2),
            "mx_key_count": 12,
            "key_pitch": 19.0,
            "keycap_nominal_gap": 1.8,
            "keycap_finish": "black_smoke_translucent",
            "keycap_legend": "none",
            "ptt_key_id": 11,
            "ptt_default_action": "push_to_talk",
            "ptt_keycap_width": PTT_KEYCAP_2U[0],
            "ptt_stabilizer": "Gateron KS-52B200T-01 2u fit-check candidate",
            "ptt_stabilizer_center_spacing": 23.8,
            "ptt_stabilizer_plate_cutout": STABILIZER_CUTOUT,
            "touch_to_ptt_center_pitch": 28.5,
            "touch_recess_to_ptt_cutout_ligament": 12.4,
            "touch_recess_to_ptt_keycap_edge_gap": 1.4,
            "c30_clearance_to_plate_bottom": round(
                BOTTOM_H + PLATE_LEDGE_H - (MAIN_PCB_Z + PCB_THICKNESS + 2.8), 2
            ),
            "encoder_body_candidate": "Alps EC11E15244G1",
            "navigation_candidate": "Alps RKJXM1015004",
            "control_body_clearance": CONTROL_BODY_CLEARANCE,
        },
        "openings": {
            "encoder_diameter": ENCODER_HOLE_D,
            "navigation_diameter": NAV_HOLE_D,
            "navigation_candidate_body_diameter": NAV_BODY_D,
            "navigation_body_radial_clearance": round((NAV_HOLE_D - NAV_BODY_D) / 2.0, 2),
            "navigation_cap_diameter": NAV_CAP_D,
            "navigation_cap_height": NAV_CAP_H,
            "touch_recess_diameter": TOUCH_RECESS_D,
            "usb_slot_center_y": USB_CENTER_Y,
            "usb_slot_width": USB_SLOT_W,
            "usb_slot_height": USB_SLOT_H,
            "usb_slot_bottom_z": USB_SLOT_Z0,
        },
        "fit_check_exclusions": [
            "Configured HLE/TSM suffix samples and actual mating force/tolerance",
            "XIAO USB shell protrusion, plug strain relief, U.FL cable bend, and shield maximum height",
            "Battery lead/protection-board protrusion, adhesive process, and swelling under charge cycling",
            "RKJXM formal supply specification and production cap attachment",
            "Gateron stabilizer screw/washer stack and first-article plate retention",
        ],
        "mesh_validation": stats,
    }
    (EXPORT_DIR / "dimensions.json").write_text(json.dumps(dimensions, indent=2) + "\n", encoding="utf-8")

    bottom_mat = make_material("bottom_charcoal", (0.045, 0.052, 0.065, 1.0), metallic=0.15, roughness=0.32)
    bezel_mat = make_material("bezel_black", (0.018, 0.022, 0.028, 1.0), metallic=0.25, roughness=0.25)
    plate_mat = make_material("plate_graphite", (0.12, 0.135, 0.16, 1.0), metallic=0.55, roughness=0.24)
    assign_material(bottom, bottom_mat)
    assign_material(bezel, bezel_mat)
    assign_material(plate, plate_mat)

    bezel.location.z = BOTTOM_H
    plate.location.z = BOTTOM_H + PLATE_LEDGE_H
    proxies = add_render_proxies(BOTTOM_H + PLATE_LEDGE_H + PLATE_T)
    camera = setup_render()
    for obj in proxies["fit_envelopes"]:
        obj.hide_render = True
    render(IMAGE_DIR / "agent-deck-v1-enclosure-assembled.png")

    # Internal stack evidence with the upper enclosure removed and the main
    # board lifted temporarily so the battery and MCU adapter stay visible.
    for obj in [bezel, plate] + proxies["controls"]:
        obj.hide_render = True
    for obj in proxies["fit_envelopes"]:
        obj.hide_render = False
    for obj in proxies["adapter"] + proxies["fit_envelopes"]:
        obj.location.z += 6.0
    for obj in proxies["main"]:
        obj.location.z += 20.0
    camera.location = (174.0, -116.0, 112.0)
    point_camera(camera, (CASE_CX, CASE_CY, 24.0))
    render(IMAGE_DIR / "agent-deck-v1-internal-stack.png")
    for obj in proxies["adapter"] + proxies["fit_envelopes"]:
        obj.location.z -= 6.0
    for obj in proxies["main"]:
        obj.location.z -= 20.0
    for obj in [bezel, plate] + proxies["controls"]:
        obj.hide_render = False
    for obj in proxies["fit_envelopes"]:
        obj.hide_render = True

    # Orthographic evidence render: this is the least ambiguous view for
    # checking the public-facing encoder–two-key–navigation control map.
    scene = bpy.context.scene
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 124.0
    camera.location = (CASE_CX, CASE_CY, 190.0)
    point_camera(camera, (CASE_CX, CASE_CY, 8.0))
    scene.render.resolution_x = 1400
    scene.render.resolution_y = 1400
    render(IMAGE_DIR / "agent-deck-v1-controls-top.png")

    # Exploded view keeps the same X/Y datums so fit relationships remain obvious.
    for obj in proxies["battery"]:
        obj.location.z += 8.0
    for obj in proxies["adapter"]:
        obj.location.z += 20.0
    for obj in proxies["fit_envelopes"]:
        obj.location.z += 20.0
        obj.hide_render = False
    for obj in proxies["main"]:
        obj.location.z += 40.0
    assembled_plate_z = BOTTOM_H + PLATE_LEDGE_H
    bezel.location.z = 66.0
    plate.location.z = 82.0
    control_delta = plate.location.z - assembled_plate_z
    for control in proxies["controls"]:
        control.location.z += control_delta
    camera.data.type = "PERSP"
    camera.data.lens = 58.0
    camera.location = (205.0, -165.0, 205.0)
    point_camera(camera, (CASE_CX, CASE_CY, 45.0))
    scene.render.resolution_x = 1800
    scene.render.resolution_y = 1200
    render(IMAGE_DIR / "agent-deck-v1-enclosure-exploded.png")

    bpy.ops.wm.save_as_mainfile(filepath=str(ARTIFACT_DIR / "agent-deck-v1-fit-check.blend"))
    print(json.dumps(dimensions, indent=2))


if __name__ == "__main__":
    main()
