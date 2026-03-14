import math
import bpy


def smooth(obj):
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.shade_smooth()
    obj.select_set(False)


def add_panel(name, size, location, material):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=location)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = (size[0] * 0.5, size[1] * 0.5, size[2] * 0.5)
    smooth(obj)
    if material:
        from common import apply_material
        apply_material(obj, material)
    return obj


def add_wheel(name, radius, width, location, material):
    bpy.ops.mesh.primitive_cylinder_add(
        radius=radius,
        depth=width,
        location=location,
        rotation=(math.radians(90), 0, 0),
    )
    obj = bpy.context.active_object
    obj.name = name
    smooth(obj)
    if material:
        from common import apply_material
        apply_material(obj, material)
    return obj


def add_well_cutter(name, radius, width, location):
    bpy.ops.mesh.primitive_cylinder_add(
        radius=radius,
        depth=width,
        location=location,
        rotation=(math.radians(90), 0, 0),
    )
    obj = bpy.context.active_object
    obj.name = name
    obj.hide_render = True
    obj.hide_viewport = True
    return obj
