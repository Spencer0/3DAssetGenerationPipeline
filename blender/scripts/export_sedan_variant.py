import os
import sys
import bpy

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from common import parse_args, get_palette_material, apply_material

BASE_BLEND = "blender/car_sedan_base.blend"
BASE_LENGTH = 3.8
BASE_WHEELBASE = 2.4


def get(name):
    return bpy.data.objects.get(name)


def apply_scale_x(obj, factor):
    if obj:
        obj.scale.x *= factor


def apply_scale_z(obj, factor):
    if obj:
        obj.scale.z *= factor


def move_x(obj, delta):
    if obj:
        obj.location.x += delta


def apply_modifiers(obj):
    if not obj:
        return
    bpy.context.view_layer.objects.active = obj
    for mod in list(obj.modifiers):
        try:
            bpy.ops.object.modifier_apply(modifier=mod.name)
        except Exception:
            pass


def main():
    args = parse_args({
        "out": "threejs-test/assets/car_sedan.glb",
        "length": 3.8,
        "roof_height": 1.0,
        "wheelbase": 2.4,
        "cabin_offset": 0.0,
        "bumper_depth": 0.0,
        "body_color": "matte_red",
    })

    bpy.ops.wm.open_mainfile(filepath=BASE_BLEND)

    length_factor = args.length / BASE_LENGTH
    wheel_delta = (args.wheelbase - BASE_WHEELBASE) * 0.5

    # Scale main body components in X
    for name in [
        "body", "hood", "cabin",
        "trim_left", "trim_right",
        "bumper_front", "bumper_rear",
        "grill", "light_l", "light_r",
        "window_left", "window_right", "window_front", "window_rear",
    ]:
        apply_scale_x(get(name), length_factor)

    # Cabin vertical scaling
    apply_scale_z(get("cabin"), args.roof_height)
    apply_scale_z(get("window_left"), args.roof_height)
    apply_scale_z(get("window_right"), args.roof_height)
    apply_scale_z(get("window_front"), args.roof_height)
    apply_scale_z(get("window_rear"), args.roof_height)

    # Cabin offset
    move_x(get("cabin"), args.cabin_offset)
    move_x(get("window_left"), args.cabin_offset)
    move_x(get("window_right"), args.cabin_offset)
    move_x(get("window_front"), args.cabin_offset)
    move_x(get("window_rear"), args.cabin_offset)

    # Bumper depth offset
    move_x(get("bumper_front"), args.bumper_depth)
    move_x(get("bumper_rear"), -args.bumper_depth)

    # Wheelbase adjustment
    for name in ["wheel_front_l", "wheel_front_r", "well_front_l", "well_front_r"]:
        move_x(get(name), wheel_delta)
    for name in ["wheel_rear_l", "wheel_rear_r", "well_rear_l", "well_rear_r"]:
        move_x(get(name), -wheel_delta)

    # Apply body color
    body = get("body")
    if body:
        apply_material(body, get_palette_material(args.body_color))

    # Apply boolean modifiers after moving cutters
    apply_modifiers(get("body"))

    # Export
    bpy.ops.export_scene.gltf(
        filepath=args.out,
        export_format='GLB',
        use_selection=False,
        export_apply=True,
        export_materials='EXPORT',
    )


if __name__ == "__main__":
    main()
