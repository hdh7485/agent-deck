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
PCB_W = 118.0
PCB_D = 118.0
PCB_THICKNESS = 1.6
MOUNT_HOLES = [(5.0, 5.0), (113.0, 5.0), (5.0, 113.0), (113.0, 113.0)]
KEY_POSITIONS = [
    (47.0, 81.0),
    (66.0, 81.0),
    (28.0, 62.0),
    (47.0, 62.0),
    (66.0, 62.0),
    (85.0, 62.0),
    (28.0, 43.0),
    (47.0, 43.0),
    (66.0, 43.0),
    (85.0, 43.0),
    (56.5, 24.0),
    (85.0, 24.0),
]
ENCODER_POS = (24.0, 81.0)
NAV_POS = (85.0, 81.0)
TOUCH_POS = (28.0, 24.0)

# Fit-check enclosure parameters.  These remain provisional until exact parts
# and the adapter/USB orientation are mechanically frozen.
CLEARANCE = 1.5
WALL = 2.4
BASE_T = 2.4
BOTTOM_H = 10.0
PCB_STANDOFF = 5.5
OUTER_W = PCB_W + 2.0 * (CLEARANCE + WALL)
OUTER_D = PCB_D + 2.0 * (CLEARANCE + WALL)
CASE_CX = PCB_W / 2.0
CASE_CY = PCB_D / 2.0
CASE_RADIUS = 5.0

PLATE_W = PCB_W + 0.8
PLATE_D = PCB_D + 0.8
PLATE_T = 1.5
PLATE_RADIUS = 3.2
PLATE_LEDGE_H = 2.0
BEZEL_H = 7.0
MX_CUTOUT = 14.2
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
TOP_BOSS_D = 10.0
USB_SERVICE_W = 26.0
USB_SERVICE_H = 7.6


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

    service_slot = cube(
        "provisional_usb_service_slot",
        (WALL * 4.0, USB_SERVICE_W, USB_SERVICE_H + 1.0),
        (
            CASE_CX + OUTER_W / 2.0 - WALL / 2.0,
            CASE_CY,
            BASE_T + (USB_SERVICE_H + 1.0) / 2.0,
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


def add_render_proxies(plate_top_z: float) -> dict[str, list[bpy.types.Object] | bpy.types.Object]:
    pcb = rounded_prism(
        "pcb_proxy",
        PCB_W,
        PCB_D,
        PCB_THICKNESS,
        center=(CASE_CX, CASE_CY),
        z0=PCB_STANDOFF,
        radius=4.0,
    )
    pcb_mat = make_material("pcb_green", (0.035, 0.19, 0.12, 1.0), metallic=0.05, roughness=0.35)
    assign_material(pcb, pcb_mat)

    # C30 candidate at PCB-local (56, 108): 7.3 x 4.3 x 2.8 mm.  The proxy
    # makes the remaining plate clearance visible in the exploded render.
    c30 = cube(
        "c30_low_profile_proxy",
        (7.3, 4.3, 2.8),
        (56.0, 108.0, PCB_STANDOFF + PCB_THICKNESS + 1.4),
    )
    add_bevel(c30, width=0.35, segments=3)
    assign_material(c30, make_material("polymer_cap", (0.82, 0.43, 0.055, 1.0), metallic=0.18, roughness=0.28))

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
    # A shallow spherical subtraction produces the low, concave thumb surface
    # visible on the public exterior reference without assuming its internal
    # switch, cap attachment, or exact dimensions.
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
    return {"pcb": pcb, "pcb_components": [c30], "controls": keycaps + [knob, nav, touch]}


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

    bpy.ops.object.camera_add(location=(205.0, -145.0, 145.0))
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
            "pcb_standoff": PCB_STANDOFF,
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
            "ptt_stabilizer": "TBD_AFTER_SAMPLE_SELECTION",
            "touch_to_ptt_center_pitch": 28.5,
            "touch_recess_to_ptt_cutout_ligament": 12.4,
            "touch_recess_to_ptt_keycap_edge_gap": 1.4,
            "c30_clearance_to_plate_bottom": round(
                BOTTOM_H + PLATE_LEDGE_H - (PCB_STANDOFF + PCB_THICKNESS + 2.8), 2
            ),
        },
        "provisional_openings": {
            "encoder_diameter": ENCODER_HOLE_D,
            "navigation_diameter": NAV_HOLE_D,
            "navigation_candidate_body_diameter": NAV_BODY_D,
            "navigation_body_radial_clearance": round((NAV_HOLE_D - NAV_BODY_D) / 2.0, 2),
            "navigation_cap_diameter": NAV_CAP_D,
            "navigation_cap_height": NAV_CAP_H,
            "touch_recess_diameter": TOUCH_RECESS_D,
            "usb_service_width": USB_SERVICE_W,
            "usb_service_height": USB_SERVICE_H,
        },
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
    render(IMAGE_DIR / "agent-deck-v1-enclosure-assembled.png")

    # Orthographic evidence render: this is the least ambiguous view for
    # checking the public-facing encoder–two-key–navigation control map.
    scene = bpy.context.scene
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 142.0
    camera.location = (CASE_CX, CASE_CY, 190.0)
    point_camera(camera, (CASE_CX, CASE_CY, 8.0))
    scene.render.resolution_x = 1400
    scene.render.resolution_y = 1400
    render(IMAGE_DIR / "agent-deck-v1-controls-top.png")

    # Exploded view keeps the same X/Y datums so fit relationships remain obvious.
    pcb = proxies["pcb"]
    pcb_components = proxies["pcb_components"]
    controls = proxies["controls"]
    assert isinstance(pcb, bpy.types.Object)
    assert isinstance(pcb_components, list)
    assert isinstance(controls, list)
    pcb.location.z += 13.0
    for component in pcb_components:
        component.location.z += 13.0
    bezel.location.z = 31.0
    plate.location.z = 46.0
    for control in controls:
        control.location.z += 34.0
    camera.data.type = "PERSP"
    camera.data.lens = 58.0
    camera.location = (215.0, -165.0, 185.0)
    point_camera(camera, (CASE_CX, CASE_CY, 25.0))
    scene.render.resolution_x = 1800
    scene.render.resolution_y = 1200
    render(IMAGE_DIR / "agent-deck-v1-enclosure-exploded.png")

    bpy.ops.wm.save_as_mainfile(filepath=str(ARTIFACT_DIR / "agent-deck-v1-fit-check.blend"))
    print(json.dumps(dimensions, indent=2))


if __name__ == "__main__":
    main()
