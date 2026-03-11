import bpy
from common import set_scene_defaults, build_palette_library, parse_args


def main():
    args = parse_args({
        "out": "blender/palette_library.blend",
    })

    set_scene_defaults()
    build_palette_library()

    bpy.ops.wm.save_as_mainfile(filepath=args.out)


if __name__ == "__main__":
    main()
