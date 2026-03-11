import math
import bpy
from common import set_scene_defaults, get_palette_material, apply_material


def main():
    set_scene_defaults()

    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.12, location=(0, 0, 0.12))
    ball = bpy.context.active_object

    # Seams as thin tori
    bpy.ops.mesh.primitive_torus_add(major_radius=0.12, minor_radius=0.004, location=(0, 0, 0.12))
    seam1 = bpy.context.active_object

    bpy.ops.mesh.primitive_torus_add(major_radius=0.12, minor_radius=0.004, location=(0, 0, 0.12), rotation=(math.radians(90), 0, 0))
    seam2 = bpy.context.active_object

    bpy.ops.mesh.primitive_torus_add(major_radius=0.12, minor_radius=0.004, location=(0, 0, 0.12), rotation=(0, math.radians(90), 0))
    seam3 = bpy.context.active_object

    mat_ball = get_palette_material("matte_red")
    mat_seam = get_palette_material("matte_charcoal")

    apply_material(ball, mat_ball)
    apply_material(seam1, mat_seam)
    apply_material(seam2, mat_seam)
    apply_material(seam3, mat_seam)


if __name__ == "__main__":
    main()
