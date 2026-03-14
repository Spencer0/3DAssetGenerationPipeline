import os
import sys
import bpy
import bmesh

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from common import set_scene_defaults, get_palette_material, apply_material, add_bevel, apply_transforms
from car_common import smooth, add_panel, add_wheel, add_well_cutter

BLEND_OUT = "blender/car_truck_base.blend"


def make_truck_shell(name, width):
    # Pickup side profile (X,Z), front at +X
    profile = [
        (-2.1, 0.0),
        (2.2, 0.0),
        (2.2, 0.6),
        (1.6, 0.85),
        (1.0, 1.25),
        (0.2, 1.25),
        (-0.2, 1.0),   # cab back drop
        (-0.6, 0.85),  # bed top start (flat)
        (-2.1, 0.85),  # bed top end
        (-2.1, 0.6),
    ]

    mesh = bpy.data.meshes.new(name + "_mesh")
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    bm = bmesh.new()

    verts = [bm.verts.new((x, 0.0, z)) for x, z in profile]
    bm.faces.new(verts)
    bm.normal_update()

    res = bmesh.ops.extrude_face_region(bm, geom=bm.faces[:])
    geom_extrude = res["geom"]
    verts_extrude = [ele for ele in geom_extrude if isinstance(ele, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, verts=verts_extrude, vec=(0.0, width, 0.0))

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

    body = make_truck_shell("body", width=1.8)
    apply_material(body, mat_body)
    add_bevel(body, width=0.07, segments=3)

    # Bumpers
    add_panel("bumper_front", (0.5, 1.6, 0.2), (2.25, 0.0, 0.2), mat_bumper)
    add_panel("bumper_rear", (0.5, 1.6, 0.2), (-2.2, 0.0, 0.2), mat_bumper)

    # Grill + lights
    add_panel("grill", (0.2, 0.9, 0.35), (2.05, 0.0, 0.55), mat_trim)
    add_panel("light_l", (0.08, 0.18, 0.18), (2.05, 0.6, 0.55), mat_light)
    add_panel("light_r", (0.08, 0.18, 0.18), (2.05, -0.6, 0.55), mat_light)

    # Windows (cab only)
    add_panel("window_left", (0.8, 0.04, 0.45), (1.0, 0.82, 1.05), mat_window)
    add_panel("window_right", (0.8, 0.04, 0.45), (1.0, -0.82, 1.05), mat_window)
    add_panel("window_front", (0.3, 0.9, 0.45), (0.6, 0.0, 1.05), mat_window)

    # Side trim
    add_panel("trim_left", (3.4, 0.04, 0.06), (0.0, 0.9, 0.5), mat_trim)
    add_panel("trim_right", (3.4, 0.04, 0.06), (0.0, -0.9, 0.5), mat_trim)

    # Wheel wells
    well_front_l = add_well_cutter("well_front_l", 0.35, 0.6, (1.5, 0.82, 0.32))
    well_front_r = add_well_cutter("well_front_r", 0.35, 0.6, (1.5, -0.82, 0.32))
    well_rear_l = add_well_cutter("well_rear_l", 0.35, 0.6, (-1.5, 0.82, 0.32))
    well_rear_r = add_well_cutter("well_rear_r", 0.35, 0.6, (-1.5, -0.82, 0.32))

    for cutter in (well_front_l, well_front_r, well_rear_l, well_rear_r):
        mod = body.modifiers.new(name=f"Well_{cutter.name}", type="BOOLEAN")
        mod.operation = 'DIFFERENCE'
        mod.object = cutter

    # Wheels
    add_wheel("wheel_front_l", 0.28, 0.18, (1.5, 0.86, 0.28), mat_wheel)
    add_wheel("wheel_front_r", 0.28, 0.18, (1.5, -0.86, 0.28), mat_wheel)
    add_wheel("wheel_rear_l", 0.28, 0.18, (-1.5, 0.86, 0.28), mat_wheel)
    add_wheel("wheel_rear_r", 0.28, 0.18, (-1.5, -0.86, 0.28), mat_wheel)

    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH':
            apply_transforms(obj)

    bpy.ops.wm.save_as_mainfile(filepath=BLEND_OUT)


if __name__ == "__main__":
    main()
