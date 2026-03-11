import os
import sys
import bpy

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from common import parse_args, get_palette_material, apply_material

BASE_BLEND = "blender/car_truck_base.blend"


def get(name):
    return bpy.data.objects.get(name)


def main():
    args = parse_args({
        "out": "threejs-test/assets/car_truck.glb",
        "body_color": "matte_red",
    })

    bpy.ops.wm.open_mainfile(filepath=BASE_BLEND)

    body = get("body")
    if body:
        apply_material(body, get_palette_material(args.body_color))

    bpy.ops.export_scene.gltf(
        filepath=args.out,
        export_format='GLB',
        use_selection=False,
        export_apply=True,
        export_materials='EXPORT',
    )


if __name__ == "__main__":
    main()
