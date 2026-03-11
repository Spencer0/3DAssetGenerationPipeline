import bpy
from common import set_scene_defaults, get_palette_material, apply_material, add_bevel


def main():
    set_scene_defaults()

    # Body
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 0.5))
    body = bpy.context.active_object
    body.scale = (0.5, 0.25, 1.0)
    add_bevel(body, width=0.02, segments=2)

    # Body scale Y is 0.25, so front face is at +0.125
    front_y = 0.125
    inset = -0.005

    # Display window (product area)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, front_y - inset, 0.55))
    display = bpy.context.active_object
    display.scale = (0.30, 0.02, 0.60)

    # Selection window (top)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, front_y - inset, 0.9))
    window = bpy.context.active_object
    window.scale = (0.26, 0.02, 0.22)

    # Button column (inset)
    buttons = []
    for i in range(4):
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.18, front_y - inset, 0.70 - i * 0.12))
        b = bpy.context.active_object
        b.scale = (0.05, 0.02, 0.04)
        buttons.append(b)

    mat_body = get_palette_material("matte_sky")
    mat_window = get_palette_material("matte_cream")
    mat_button = get_palette_material("matte_red")

    apply_material(body, mat_body)
    apply_material(window, mat_window)
    apply_material(display, mat_window)
    for b in buttons:
        apply_material(b, mat_button)


if __name__ == "__main__":
    main()
