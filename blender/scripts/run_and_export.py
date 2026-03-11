import os
import sys
import shlex
import runpy
import bpy

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from common import parse_args


def main():
    args = parse_args({
        "script": "",
        "out": "export.glb",
        "script_args": "",
    })

    if not args.script:
        print("Missing --script path")
        return

    script_path = os.path.abspath(args.script)
    script_dir = os.path.dirname(script_path)
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)
    # Isolate args so the target script won't see run_and_export arguments.
    old_argv = sys.argv[:]
    extra = shlex.split(args.script_args) if args.script_args else []
    sys.argv = [script_path] + extra
    try:
        runpy.run_path(script_path, run_name="__main__")
    finally:
        sys.argv = old_argv

    bpy.ops.export_scene.gltf(
        filepath=args.out,
        export_format='GLB',
        use_selection=False,
        export_apply=True,
        export_materials='EXPORT',
    )


if __name__ == "__main__":
    main()
