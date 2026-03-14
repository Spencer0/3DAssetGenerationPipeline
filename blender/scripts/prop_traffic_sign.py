import os
import sys
import math
import bpy

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from common import set_scene_defaults, parse_args, get_palette_material, apply_material, add_bevel


EPS = 0.002


def add_pole(radius, height):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=height, location=(0, 0, height * 0.5))
    pole = bpy.context.active_object
    pole.name = "pole"
    return pole


def add_stop_sign(size, thickness, pole_radius, z_center, mat_body, mat_face):
    # 8-sided prism
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=8,
        radius=size * 0.5,
        depth=thickness,
        location=(0, pole_radius + thickness * 0.5 + EPS, z_center),
        rotation=(math.radians(90), 0, 0),
    )
    body = bpy.context.active_object
    body.name = "sign_body"
    apply_material(body, mat_body)

    # Front face panel, slightly inset
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=8,
        radius=size * 0.44,
        depth=0.02,
        location=(0, pole_radius + thickness + 0.01 + EPS, z_center),
        rotation=(math.radians(90), 0, 0),
    )
    face = bpy.context.active_object
    face.name = "sign_face"
    apply_material(face, mat_face)


def add_triangle_sign(size, thickness, pole_radius, z_center, mat_body, mat_face):
    # 3-sided prism
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=3,
        radius=size * 0.58,
        depth=thickness,
        location=(0, pole_radius + thickness * 0.5 + EPS, z_center),
        rotation=(math.radians(90), 0, math.radians(90)),
    )
    body = bpy.context.active_object
    body.name = "sign_body"
    apply_material(body, mat_body)

    bpy.ops.mesh.primitive_cylinder_add(
        vertices=3,
        radius=size * 0.50,
        depth=0.02,
        location=(0, pole_radius + thickness + 0.01 + EPS, z_center),
        rotation=(math.radians(90), 0, math.radians(90)),
    )
    face = bpy.context.active_object
    face.name = "sign_face"
    apply_material(face, mat_face)


def add_square_sign(size, thickness, pole_radius, z_center, mat_body, mat_face):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, pole_radius + thickness * 0.5 + EPS, z_center))
    body = bpy.context.active_object
    body.name = "sign_body"
    body.scale = (size * 0.5, thickness * 0.5, size * 0.5)
    add_bevel(body, width=0.02, segments=2)
    apply_material(body, mat_body)

    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, pole_radius + thickness + 0.01 + EPS, z_center))
    face = bpy.context.active_object
    face.name = "sign_face"
    face.scale = (size * 0.44, 0.01, size * 0.44)
    apply_material(face, mat_face)


def main():
    args = parse_args({
        "variant": "stop",
        "out": "",
        "pole_height": 2.2,
        "pole_radius": 0.045,
        "sign_size": 0.7,
        "sign_thickness": 0.06,
    })

    set_scene_defaults()

    pole = add_pole(args.pole_radius, args.pole_height)
    apply_material(pole, get_palette_material("matte_charcoal"))

    # Place sign just above the pole top with a slight gap.
    sign_center_z = args.pole_height - (args.sign_size * 0.5) + 0.08

    variant = (args.variant or "").lower()
    if variant == "stop":
        add_stop_sign(
            args.sign_size,
            args.sign_thickness,
            args.pole_radius,
            sign_center_z,
            get_palette_material("matte_red"),
            get_palette_material("matte_cream"),
        )
    elif variant in ("triangle", "warning"):
        add_triangle_sign(
            args.sign_size,
            args.sign_thickness,
            args.pole_radius,
            sign_center_z,
            get_palette_material("matte_lemon"),
            get_palette_material("matte_charcoal"),
        )
    elif variant in ("square", "speed", "speed_limit"):
        add_square_sign(
            args.sign_size,
            args.sign_thickness,
            args.pole_radius,
            sign_center_z,
            get_palette_material("matte_cream"),
            get_palette_material("matte_charcoal"),
        )
    else:
        raise ValueError("Unknown variant. Use: stop, triangle, or square.")

    if args.out:
        bpy.ops.export_scene.gltf(
            filepath=args.out,
            export_format='GLB',
            use_selection=False,
            export_apply=True,
            export_materials='EXPORT',
        )


if __name__ == "__main__":
    main()
