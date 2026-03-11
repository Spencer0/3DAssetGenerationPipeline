import bpy
from common import parse_args


def main():
    args = parse_args({
        "out": "export.glb",
        "use_selection": False,
        "apply_modifiers": True,
    })

    bpy.ops.export_scene.gltf(
        filepath=args.out,
        export_format='GLB',
        use_selection=args.use_selection,
        export_apply=args.apply_modifiers,
        export_materials='EXPORT',
    )


if __name__ == "__main__":
    main()
