import os
import sys
import bpy
import bmesh

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from common import set_scene_defaults, get_palette_material, apply_material, add_bevel, apply_transforms
from car_common import smooth, add_panel, add_wheel, add_well_cutter

BLEND_OUT = "blender/car_sedan_base.blend"


def make_body_shell(name, width):
    # Side profile (X,Z) in meters, front at +X
    profile = [
        (-1.9, 0.0),
        (1.9, 0.0),
        (1.9, 0.6),
        (1.4, 0.85),
        (0.6, 1.1),
        (-0.2, 1.1),
        (-0.9, 0.95),
        (-1.4, 0.8),
        (-1.9, 0.6),
    ]

    mesh = bpy.data.meshes.new(name + "_mesh")
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    bm = bmesh.new()

    verts = [bm.verts.new((x, 0.0, z)) for x, z in profile]
    bm.faces.new(verts)
    bm.normal_update()

    # Extrude along Y to width
    res = bmesh.ops.extrude_face_region(bm, geom=bm.faces[:])
    geom_extrude = res["geom"]
    verts_extrude = [ele for ele in geom_extrude if isinstance(ele, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, verts=verts_extrude, vec=(0.0, width, 0.0))

    # Center on Y
    bmesh.ops.translate(bm, verts=bm.verts, vec=(0.0, -width * 0.5, 0.0))

    bm.to_mesh(mesh)
    bm.free()

    smooth(obj)
    return obj




def main():
    set_scene_defaults()

    mat_body = get_palette_material("matte_red")
    mat_window = get_palette_material("matte_sky")
    mat_trim = get_palette_material("matte_charcoal")
    mat_bumper = get_palette_material("matte_asphalt")
    mat_wheel = get_palette_material("matte_charcoal")
    mat_light = get_palette_material("matte_lemon")

    body = make_body_shell("body", width=1.7)
    apply_material(body, mat_body)

    # Bevel body for roundness
    add_bevel(body, width=0.08, segments=4)

    # Bumpers
    bumper_front = add_panel("bumper_front", (0.5, 1.6, 0.2), (1.95, 0.0, 0.2), mat_bumper)
    bumper_rear = add_panel("bumper_rear", (0.4, 1.5, 0.2), (-1.95, 0.0, 0.2), mat_bumper)

    # Grill + lights
    add_panel("grill", (0.2, 0.9, 0.35), (1.85, 0.0, 0.5), mat_trim)
    add_panel("light_l", (0.08, 0.18, 0.18), (1.85, 0.6, 0.55), mat_light)
    add_panel("light_r", (0.08, 0.18, 0.18), (1.85, -0.6, 0.55), mat_light)

    # Windows (inset panels)
    add_panel("window_left", (1.1, 0.04, 0.45), (0.2, 0.78, 0.95), mat_window)
    add_panel("window_right", (1.1, 0.04, 0.45), (0.2, -0.78, 0.95), mat_window)
    add_panel("window_front", (0.4, 0.9, 0.45), (-0.6, 0.0, 0.95), mat_window)
    add_panel("window_rear", (0.4, 0.9, 0.45), (0.9, 0.0, 0.95), mat_window)

    # Side trim
    add_panel("trim_left", (3.2, 0.04, 0.06), (0.0, 0.86, 0.5), mat_trim)
    add_panel("trim_right", (3.2, 0.04, 0.06), (0.0, -0.86, 0.5), mat_trim)

    # Wheel wells (cutters + boolean mods)
    well_front_l = add_well_cutter("well_front_l", 0.35, 0.6, (1.2, 0.78, 0.32))
    well_front_r = add_well_cutter("well_front_r", 0.35, 0.6, (1.2, -0.78, 0.32))
    well_rear_l = add_well_cutter("well_rear_l", 0.35, 0.6, (-1.2, 0.78, 0.32))
    well_rear_r = add_well_cutter("well_rear_r", 0.35, 0.6, (-1.2, -0.78, 0.32))

    for cutter in (well_front_l, well_front_r, well_rear_l, well_rear_r):
        mod = body.modifiers.new(name=f"Well_{cutter.name}", type="BOOLEAN")
        mod.operation = 'DIFFERENCE'
        mod.object = cutter

    # Wheels
    add_wheel("wheel_front_l", 0.28, 0.18, (1.2, 0.82, 0.28), mat_wheel)
    add_wheel("wheel_front_r", 0.28, 0.18, (1.2, -0.82, 0.28), mat_wheel)
    add_wheel("wheel_rear_l", 0.28, 0.18, (-1.2, 0.82, 0.28), mat_wheel)
    add_wheel("wheel_rear_r", 0.28, 0.18, (-1.2, -0.82, 0.28), mat_wheel)

    # Apply transforms
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH':
            apply_transforms(obj)

    bpy.ops.wm.save_as_mainfile(filepath=BLEND_OUT)


if __name__ == "__main__":
    main()
