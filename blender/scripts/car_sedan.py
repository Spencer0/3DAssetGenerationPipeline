import math
import bpy
from common import set_scene_defaults, get_palette_material, apply_material, add_bevel


def smooth(obj):
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.shade_smooth()
    obj.select_set(False)


def add_beveled_cube(size, location, bevel=0.12, segments=4):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=location)
    obj = bpy.context.active_object
    obj.scale = (size[0] * 0.5, size[1] * 0.5, size[2] * 0.5)
    add_bevel(obj, width=bevel, segments=segments)
    smooth(obj)
    return obj


def add_panel(size, location, material):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=location)
    obj = bpy.context.active_object
    obj.scale = (size[0] * 0.5, size[1] * 0.5, size[2] * 0.5)
    smooth(obj)
    apply_material(obj, material)
    return obj


def add_wheel(radius, width, location, material):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=width, location=location, rotation=(math.radians(90), 0, 0))
    obj = bpy.context.active_object
    smooth(obj)
    apply_material(obj, material)
    return obj


def boolean_cut(target, cutter):
    mod = target.modifiers.new(name="Boolean", type="BOOLEAN")
    mod.operation = 'DIFFERENCE'
    mod.object = cutter
    bpy.context.view_layer.objects.active = target
    bpy.ops.object.modifier_apply(modifier=mod.name)
    cutter.select_set(True)
    bpy.ops.object.delete()


def main():
    set_scene_defaults()

    # Materials
    mat_body = get_palette_material("matte_red")
    mat_cabin = get_palette_material("matte_red")
    mat_window = get_palette_material("matte_sky")
    mat_trim = get_palette_material("matte_charcoal")
    mat_bumper = get_palette_material("matte_asphalt")
    mat_wheel = get_palette_material("matte_charcoal")
    mat_light = get_palette_material("matte_lemon")

    # Body base (rounded)
    body = add_beveled_cube((3.9, 1.7, 0.85), (0, 0, 0.42), bevel=0.14, segments=4)
    apply_material(body, mat_body)

    # Hood / front top
    hood = add_beveled_cube((1.5, 1.6, 0.35), (1.0, 0, 0.9), bevel=0.08, segments=3)
    apply_material(hood, mat_body)

    # Cabin (tapered by size)
    cabin = add_beveled_cube((1.9, 1.45, 0.85), (-0.1, 0, 1.2), bevel=0.08, segments=3)
    apply_material(cabin, mat_cabin)

    # Window panels (flat, inset)
    add_panel((1.2, 0.05, 0.5), (0.0, 0.78, 1.2), mat_window)
    add_panel((1.2, 0.05, 0.5), (0.0, -0.78, 1.2), mat_window)
    add_panel((0.5, 1.0, 0.5), (-0.6, 0.0, 1.2), mat_window)
    add_panel((0.5, 1.0, 0.5), (0.7, 0.0, 1.2), mat_window)

    # Side trim
    add_panel((3.2, 0.05, 0.08), (0.0, 0.86, 0.55), mat_trim)
    add_panel((3.2, 0.05, 0.08), (0.0, -0.86, 0.55), mat_trim)

    # Bumpers
    bumper_front = add_beveled_cube((3.7, 0.35, 0.25), (1.8, 0, 0.18), bevel=0.04, segments=2)
    bumper_back = add_beveled_cube((3.2, 0.35, 0.25), (-1.8, 0, 0.18), bevel=0.04, segments=2)
    apply_material(bumper_front, mat_bumper)
    apply_material(bumper_back, mat_bumper)

    # Grill and lights
    add_panel((0.6, 0.1, 0.4), (1.95, 0.0, 0.55), mat_trim)
    add_panel((0.18, 0.08, 0.18), (1.95, 0.6, 0.55), mat_light)
    add_panel((0.18, 0.08, 0.18), (1.95, -0.6, 0.55), mat_light)

    # Wheel wells (boolean cuts)
    for x in (-1.2, 1.2):
        for y in (-0.78, 0.78):
            bpy.ops.mesh.primitive_cylinder_add(radius=0.35, depth=0.6, location=(x, y, 0.32), rotation=(math.radians(90), 0, 0))
            cutter = bpy.context.active_object
            boolean_cut(body, cutter)

    # Wheels
    add_wheel(0.28, 0.18, (-1.2, 0.82, 0.28), mat_wheel)
    add_wheel(0.28, 0.18, (1.2, 0.82, 0.28), mat_wheel)
    add_wheel(0.28, 0.18, (-1.2, -0.82, 0.28), mat_wheel)
    add_wheel(0.28, 0.18, (1.2, -0.82, 0.28), mat_wheel)


if __name__ == "__main__":
    main()
