import bpy
from common import set_scene_defaults, get_palette_material, apply_material, add_bevel


def main():
    set_scene_defaults()

    # Fruit body
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.06, location=(0, 0, 0.06))
    body = bpy.context.active_object
    body.scale = (1.0, 1.1, 0.9)
    add_bevel(body, width=0.003, segments=2)

    # Stem
    bpy.ops.mesh.primitive_cylinder_add(radius=0.008, depth=0.03, location=(0, 0, 0.12))
    stem = bpy.context.active_object

    mat_body = get_palette_material("matte_lemon")
    mat_stem = get_palette_material("matte_mint")

    apply_material(body, mat_body)
    apply_material(stem, mat_stem)


if __name__ == "__main__":
    main()
