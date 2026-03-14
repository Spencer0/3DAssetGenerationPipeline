import os
import sys
import bpy

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from common import set_scene_defaults, parse_args, get_palette_material, add_group_input, add_group_output


def build_store_group(args):
    ng = bpy.data.node_groups.new("GN_Store", "GeometryNodeTree")
    add_group_input(ng, "Width", "NodeSocketFloat", args.width)
    add_group_input(ng, "Depth", "NodeSocketFloat", args.depth)
    add_group_input(ng, "Height", "NodeSocketFloat", args.height)
    add_group_input(ng, "Roof Overhang", "NodeSocketFloat", args.roof_overhang)
    add_group_input(ng, "Window Depth", "NodeSocketFloat", args.window_depth)
    add_group_input(ng, "Window Height", "NodeSocketFloat", args.window_height)
    add_group_input(ng, "Window Sill", "NodeSocketFloat", args.window_sill)
    add_group_input(ng, "Door Width", "NodeSocketFloat", args.door_width)
    add_group_input(ng, "Door Height", "NodeSocketFloat", args.door_height)
    add_group_input(ng, "Sign Width", "NodeSocketFloat", args.sign_width)
    add_group_input(ng, "Sign Height", "NodeSocketFloat", args.sign_height)
    add_group_output(ng, "Geometry", "NodeSocketGeometry")

    nodes = ng.nodes
    links = ng.links

    inp = nodes.new("NodeGroupInput")
    out = nodes.new("NodeGroupOutput")

    # Body
    body = nodes.new("GeometryNodeMeshCube")
    body_xform = nodes.new("GeometryNodeTransform")
    body_mat = nodes.new("GeometryNodeSetMaterial")

    body_scale = nodes.new("ShaderNodeCombineXYZ")
    links.new(inp.outputs["Width"], body_scale.inputs["X"])
    links.new(inp.outputs["Depth"], body_scale.inputs["Y"])
    links.new(inp.outputs["Height"], body_scale.inputs["Z"])
    links.new(body_scale.outputs["Vector"], body_xform.inputs["Scale"])

    body_z = nodes.new("ShaderNodeMath")
    body_z.operation = "MULTIPLY"
    links.new(inp.outputs["Height"], body_z.inputs[0])
    body_z.inputs[1].default_value = 0.5
    body_pos = nodes.new("ShaderNodeCombineXYZ")
    links.new(body_z.outputs[0], body_pos.inputs["Z"])
    links.new(body_pos.outputs["Vector"], body_xform.inputs["Translation"])

    links.new(body.outputs["Mesh"], body_xform.inputs["Geometry"])
    links.new(body_xform.outputs["Geometry"], body_mat.inputs["Geometry"])

    # Roof (flat with overhang)
    roof = nodes.new("GeometryNodeMeshCube")
    roof_xform = nodes.new("GeometryNodeTransform")
    roof_mat = nodes.new("GeometryNodeSetMaterial")

    roof_over = nodes.new("ShaderNodeMath")
    roof_over.operation = "MULTIPLY"
    links.new(inp.outputs["Roof Overhang"], roof_over.inputs[0])
    roof_over.inputs[1].default_value = 2.0

    roof_w = nodes.new("ShaderNodeMath")
    roof_w.operation = "ADD"
    links.new(inp.outputs["Width"], roof_w.inputs[0])
    links.new(roof_over.outputs[0], roof_w.inputs[1])

    roof_d = nodes.new("ShaderNodeMath")
    roof_d.operation = "ADD"
    links.new(inp.outputs["Depth"], roof_d.inputs[0])
    links.new(roof_over.outputs[0], roof_d.inputs[1])

    roof_scale = nodes.new("ShaderNodeCombineXYZ")
    links.new(roof_w.outputs[0], roof_scale.inputs["X"])
    links.new(roof_d.outputs[0], roof_scale.inputs["Y"])
    roof_scale.inputs["Z"].default_value = 0.4
    links.new(roof_scale.outputs["Vector"], roof_xform.inputs["Scale"])

    roof_z = nodes.new("ShaderNodeMath")
    roof_z.operation = "ADD"
    links.new(inp.outputs["Height"], roof_z.inputs[0])
    roof_z.inputs[1].default_value = 0.2
    roof_pos = nodes.new("ShaderNodeCombineXYZ")
    links.new(roof_z.outputs[0], roof_pos.inputs["Z"])
    links.new(roof_pos.outputs["Vector"], roof_xform.inputs["Translation"])

    links.new(roof.outputs["Mesh"], roof_xform.inputs["Geometry"])
    links.new(roof_xform.outputs["Geometry"], roof_mat.inputs["Geometry"])

    # Front windows: 4 on each side of the door (explicit positions for centering)
    win = nodes.new("GeometryNodeMeshCube")
    win_scale = nodes.new("ShaderNodeCombineXYZ")
    win_width = 1.2
    win_scale.inputs["X"].default_value = win_width
    links.new(inp.outputs["Window Depth"], win_scale.inputs["Y"])

    win_h70 = nodes.new("ShaderNodeMath")
    win_h70.operation = "MULTIPLY"
    links.new(inp.outputs["Height"], win_h70.inputs[0])
    win_h70.inputs[1].default_value = 0.7
    links.new(win_h70.outputs[0], win_scale.inputs["Z"])

    win_mat = nodes.new("GeometryNodeSetMaterial")

    # Position left/right window groups
    front_y = nodes.new("ShaderNodeMath")
    front_y.operation = "ADD"
    depth_half = nodes.new("ShaderNodeMath")
    depth_half.operation = "MULTIPLY"
    links.new(inp.outputs["Depth"], depth_half.inputs[0])
    depth_half.inputs[1].default_value = 0.5
    win_depth_half = nodes.new("ShaderNodeMath")
    win_depth_half.operation = "MULTIPLY"
    links.new(inp.outputs["Window Depth"], win_depth_half.inputs[0])
    win_depth_half.inputs[1].default_value = 0.5
    links.new(depth_half.outputs[0], front_y.inputs[0])
    links.new(win_depth_half.outputs[0], front_y.inputs[1])
    front_y2 = nodes.new("ShaderNodeMath")
    front_y2.operation = "SUBTRACT"
    links.new(front_y.outputs[0], front_y2.inputs[0])
    front_y2.inputs[1].default_value = 0.01

    win_z = nodes.new("ShaderNodeMath")
    win_z.operation = "MULTIPLY"
    links.new(inp.outputs["Height"], win_z.inputs[0])
    win_z.inputs[1].default_value = 0.5

    door_half = nodes.new("ShaderNodeMath")
    door_half.operation = "MULTIPLY"
    links.new(inp.outputs["Door Width"], door_half.inputs[0])
    door_half.inputs[1].default_value = 0.5

    gap = nodes.new("ShaderNodeMath")
    gap.operation = "MULTIPLY"
    links.new(inp.outputs["Width"], gap.inputs[0])
    gap.inputs[1].default_value = 0.02

    spacing = nodes.new("ShaderNodeMath")
    spacing.operation = "ADD"
    spacing.inputs[0].default_value = win_width
    links.new(gap.outputs[0], spacing.inputs[1])

    base_offset = nodes.new("ShaderNodeMath")
    base_offset.operation = "ADD"
    links.new(door_half.outputs[0], base_offset.inputs[0])
    base_offset.inputs[1].default_value = win_width * 0.5

    base_offset2 = nodes.new("ShaderNodeMath")
    base_offset2.operation = "ADD"
    links.new(base_offset.outputs[0], base_offset2.inputs[0])
    links.new(gap.outputs[0], base_offset2.inputs[1])

    join_windows = nodes.new("GeometryNodeJoinGeometry")

    for i in range(4):
        i_mul = nodes.new("ShaderNodeMath")
        i_mul.operation = "MULTIPLY"
        links.new(spacing.outputs[0], i_mul.inputs[0])
        i_mul.inputs[1].default_value = float(i)

        offset_i = nodes.new("ShaderNodeMath")
        offset_i.operation = "ADD"
        links.new(base_offset2.outputs[0], offset_i.inputs[0])
        links.new(i_mul.outputs[0], offset_i.inputs[1])

        # Left window
        left_x = nodes.new("ShaderNodeMath")
        left_x.operation = "MULTIPLY"
        links.new(offset_i.outputs[0], left_x.inputs[0])
        left_x.inputs[1].default_value = -1.0
        left_pos = nodes.new("ShaderNodeCombineXYZ")
        links.new(left_x.outputs[0], left_pos.inputs["X"])
        links.new(front_y2.outputs[0], left_pos.inputs["Y"])
        links.new(win_z.outputs[0], left_pos.inputs["Z"])
        left_xform = nodes.new("GeometryNodeTransform")
        links.new(win.outputs["Mesh"], left_xform.inputs["Geometry"])
        links.new(win_scale.outputs["Vector"], left_xform.inputs["Scale"])
        links.new(left_pos.outputs["Vector"], left_xform.inputs["Translation"])
        links.new(left_xform.outputs["Geometry"], join_windows.inputs["Geometry"])

        # Right window
        right_pos = nodes.new("ShaderNodeCombineXYZ")
        links.new(offset_i.outputs[0], right_pos.inputs["X"])
        links.new(front_y2.outputs[0], right_pos.inputs["Y"])
        links.new(win_z.outputs[0], right_pos.inputs["Z"])
        right_xform = nodes.new("GeometryNodeTransform")
        links.new(win.outputs["Mesh"], right_xform.inputs["Geometry"])
        links.new(win_scale.outputs["Vector"], right_xform.inputs["Scale"])
        links.new(right_pos.outputs["Vector"], right_xform.inputs["Translation"])
        links.new(right_xform.outputs["Geometry"], join_windows.inputs["Geometry"])

    links.new(join_windows.outputs["Geometry"], win_mat.inputs["Geometry"])

    # Door
    door = nodes.new("GeometryNodeMeshCube")
    door_xform = nodes.new("GeometryNodeTransform")
    door_mat = nodes.new("GeometryNodeSetMaterial")

    door_scale = nodes.new("ShaderNodeCombineXYZ")
    links.new(inp.outputs["Door Width"], door_scale.inputs["X"])
    door_scale.inputs["Y"].default_value = 0.08
    links.new(inp.outputs["Door Height"], door_scale.inputs["Z"])
    links.new(door_scale.outputs["Vector"], door_xform.inputs["Scale"])

    door_z = nodes.new("ShaderNodeMath")
    door_z.operation = "MULTIPLY"
    links.new(inp.outputs["Door Height"], door_z.inputs[0])
    door_z.inputs[1].default_value = 0.5
    door_pos = nodes.new("ShaderNodeCombineXYZ")
    links.new(front_y2.outputs[0], door_pos.inputs["Y"])
    links.new(door_z.outputs[0], door_pos.inputs["Z"])
    links.new(door_pos.outputs["Vector"], door_xform.inputs["Translation"])

    links.new(door.outputs["Mesh"], door_xform.inputs["Geometry"])
    links.new(door_xform.outputs["Geometry"], door_mat.inputs["Geometry"])

    # Billboard sign
    sign = nodes.new("GeometryNodeMeshCube")
    sign_xform = nodes.new("GeometryNodeTransform")
    sign_mat = nodes.new("GeometryNodeSetMaterial")
    sign_scale = nodes.new("ShaderNodeCombineXYZ")
    links.new(inp.outputs["Sign Width"], sign_scale.inputs["X"])
    sign_scale.inputs["Y"].default_value = 0.12
    links.new(inp.outputs["Sign Height"], sign_scale.inputs["Z"])
    links.new(sign_scale.outputs["Vector"], sign_xform.inputs["Scale"])

    sign_z = nodes.new("ShaderNodeMath")
    sign_z.operation = "SUBTRACT"
    links.new(inp.outputs["Height"], sign_z.inputs[0])
    sign_z.inputs[1].default_value = 0.2
    sign_pos = nodes.new("ShaderNodeCombineXYZ")
    links.new(front_y2.outputs[0], sign_pos.inputs["Y"])
    links.new(sign_z.outputs[0], sign_pos.inputs["Z"])
    links.new(sign_pos.outputs["Vector"], sign_xform.inputs["Translation"])
    links.new(sign.outputs["Mesh"], sign_xform.inputs["Geometry"])
    links.new(sign_xform.outputs["Geometry"], sign_mat.inputs["Geometry"])

    # Join all
    join_all = nodes.new("GeometryNodeJoinGeometry")
    links.new(body_mat.outputs["Geometry"], join_all.inputs["Geometry"])
    links.new(roof_mat.outputs["Geometry"], join_all.inputs["Geometry"])
    links.new(win_mat.outputs["Geometry"], join_all.inputs["Geometry"])
    links.new(door_mat.outputs["Geometry"], join_all.inputs["Geometry"])
    links.new(sign_mat.outputs["Geometry"], join_all.inputs["Geometry"])
    links.new(join_all.outputs["Geometry"], out.inputs["Geometry"])

    return ng, body_mat, roof_mat, door_mat, sign_mat, win_mat


def main():
    args = parse_args({
        "out": "",
        "width": 14.0,
        "depth": 6.0,
        "height": 3.6,
        "roof_overhang": 0.4,
        "window_depth": 0.04,
        "window_height": 1.0,
        "window_sill": 1.1,
        "door_width": 2.0,
        "door_height": 2.2,
        "sign_width": 6.0,
        "sign_height": 1.0,
    })

    set_scene_defaults()

    mesh = bpy.data.meshes.new("store_mesh")
    mesh.from_pydata([(0, 0, 0)], [], [])
    obj = bpy.data.objects.new("store", mesh)
    bpy.context.collection.objects.link(obj)

    mat_body = get_palette_material("matte_cream")
    mat_roof = get_palette_material("matte_charcoal")
    mat_windows = get_palette_material("matte_sky")
    mat_door = get_palette_material("matte_asphalt")
    mat_sign = get_palette_material("matte_lemon")

    ng, body_mat, roof_mat, door_mat, sign_mat, win_mat = build_store_group(args)
    body_mat.inputs["Material"].default_value = mat_body
    roof_mat.inputs["Material"].default_value = mat_roof
    win_mat.inputs["Material"].default_value = mat_windows
    door_mat.inputs["Material"].default_value = mat_door
    sign_mat.inputs["Material"].default_value = mat_sign

    mod = obj.modifiers.new(name="GN_Store", type="NODES")
    mod.node_group = ng

    if args.out:
        bpy.ops.export_scene.gltf(
            filepath=args.out,
            export_format="GLB",
            use_selection=False,
            export_apply=True,
            export_materials="EXPORT",
        )


if __name__ == "__main__":
    main()
