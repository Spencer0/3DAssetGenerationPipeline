import argparse
import sys
import bpy

PALETTE = {
    "cream": (0.956, 0.906, 0.772, 1.0),
    "sakura": (0.953, 0.651, 0.722, 1.0),
    "sky": (0.498, 0.710, 0.902, 1.0),
    "mint": (0.557, 0.827, 0.710, 1.0),
    "charcoal": (0.180, 0.180, 0.200, 1.0),
    "asphalt": (0.357, 0.357, 0.388, 1.0),
    "lemon": (0.949, 0.831, 0.361, 1.0),
    "accent_red": (0.910, 0.361, 0.290, 1.0),
}

MATERIAL_LIBRARY = {
    "matte_cream": ("cream", 0.85, 0.0),
    "matte_sakura": ("sakura", 0.8, 0.0),
    "matte_sky": ("sky", 0.7, 0.0),
    "matte_mint": ("mint", 0.8, 0.0),
    "matte_charcoal": ("charcoal", 0.9, 0.0),
    "matte_asphalt": ("asphalt", 0.85, 0.0),
    "matte_lemon": ("lemon", 0.75, 0.0),
    "matte_red": ("accent_red", 0.75, 0.0),
}


def set_scene_defaults():
    scene = bpy.context.scene
    scene.unit_settings.system = 'METRIC'
    scene.unit_settings.scale_length = 1.0
    # Clear scene
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)


def parse_args(defaults):
    parser = argparse.ArgumentParser()
    for key, value in defaults.items():
        if isinstance(value, bool):
            if value:
                parser.add_argument(f"--{key}", action="store_false")
            else:
                parser.add_argument(f"--{key}", action="store_true")
        else:
            arg_type = type(value)
            parser.add_argument(f"--{key}", type=arg_type, default=value)
    if "--" in sys.argv:
        args = parser.parse_args(sys.argv[sys.argv.index("--") + 1 :])
    else:
        args = parser.parse_args(sys.argv[1:])
    return args


def create_material(name, color, roughness=0.8, metalness=0.0):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    bsdf = nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = color
        bsdf.inputs["Roughness"].default_value = roughness
        bsdf.inputs["Metallic"].default_value = metalness
    return mat


def get_palette_material(key):
    if key not in MATERIAL_LIBRARY:
        raise KeyError(f"Unknown material key: {key}")
    name = f"MAT_{key}"
    existing = bpy.data.materials.get(name)
    if existing:
        return existing
    color_key, roughness, metalness = MATERIAL_LIBRARY[key]
    return create_material(name, PALETTE[color_key], roughness=roughness, metalness=metalness)


def build_palette_library():
    for key in MATERIAL_LIBRARY.keys():
        get_palette_material(key)


def add_group_input(ng, name, socket_type, default=None):
    sock = ng.interface.new_socket(name=name, in_out='INPUT', socket_type=socket_type)
    if default is not None:
        sock.default_value = default
    return sock


def add_group_output(ng, name, socket_type):
    return ng.interface.new_socket(name=name, in_out='OUTPUT', socket_type=socket_type)


def apply_material(obj, mat):
    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)


def add_bevel(obj, width=0.02, segments=2):
    mod = obj.modifiers.new(name="Bevel", type='BEVEL')
    mod.width = width
    mod.segments = segments
    mod.profile = 0.7
    return mod


def apply_transforms(obj):
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    obj.select_set(False)
