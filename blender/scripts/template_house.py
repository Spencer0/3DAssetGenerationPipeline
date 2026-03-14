import os
import sys
import math
import bpy

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from common import set_scene_defaults, parse_args, get_palette_material, add_group_input, add_group_output


def build_house_group(args):
    ng = bpy.data.node_groups.new("GN_House", "GeometryNodeTree")
    add_group_input(ng, "Width", "NodeSocketFloat", args.width)
    add_group_input(ng, "Depth", "NodeSocketFloat", args.depth)
    add_group_input(ng, "Floors", "NodeSocketFloat", float(args.floors))
    add_group_input(ng, "Floor Height", "NodeSocketFloat", args.floor_height)
    add_group_input(ng, "Roof Height", "NodeSocketFloat", args.roof_height)
    add_group_input(ng, "Window Depth", "NodeSocketFloat", args.window_depth)
    add_group_output(ng, "Geometry", "NodeSocketGeometry")

    nodes = ng.nodes
    links = ng.links

    inp = nodes.new("NodeGroupInput")
    out = nodes.new("NodeGroupOutput")

    # Body height = floors * floor_height
    body_h = nodes.new("ShaderNodeMath")
    body_h.operation = "MULTIPLY"
    links.new(inp.outputs["Floors"], body_h.inputs[0])
    links.new(inp.outputs["Floor Height"], body_h.inputs[1])

    body = nodes.new("GeometryNodeMeshCube")
    body.inputs["Size"].default_value = (1.0, 1.0, 1.0)
    body_xform = nodes.new("GeometryNodeTransform")
    body_mat = nodes.new("GeometryNodeSetMaterial")

    # Set scale via separate node
    body_scale = nodes.new("ShaderNodeCombineXYZ")
    links.new(inp.outputs["Width"], body_scale.inputs["X"])
    links.new(inp.outputs["Depth"], body_scale.inputs["Y"])
    links.new(body_h.outputs[0], body_scale.inputs["Z"])
    links.new(body_scale.outputs["Vector"], body_xform.inputs["Scale"])

    body_z = nodes.new("ShaderNodeMath")
    body_z.operation = "MULTIPLY"
    links.new(body_h.outputs[0], body_z.inputs[0])
    body_z.inputs[1].default_value = 0.5
    body_pos = nodes.new("ShaderNodeCombineXYZ")
    links.new(body_z.outputs[0], body_pos.inputs["Z"])
    links.new(body_pos.outputs["Vector"], body_xform.inputs["Translation"])

    links.new(body.outputs["Mesh"], body_xform.inputs["Geometry"])
    links.new(body_xform.outputs["Geometry"], body_mat.inputs["Geometry"])

    # Roof: cube -> gable by collapsing top vertices to ridge
    roof = nodes.new("GeometryNodeMeshCube")
    roof_xform = nodes.new("GeometryNodeTransform")
    roof_mat = nodes.new("GeometryNodeSetMaterial")
    roof_pos = nodes.new("ShaderNodeCombineXYZ")

    roof_w = nodes.new("ShaderNodeMath")
    roof_w.operation = "MULTIPLY"
    links.new(inp.outputs["Width"], roof_w.inputs[0])
    roof_w.inputs[1].default_value = 1.05

    roof_d = nodes.new("ShaderNodeMath")
    roof_d.operation = "MULTIPLY"
    links.new(inp.outputs["Depth"], roof_d.inputs[0])
    roof_d.inputs[1].default_value = 1.05

    roof_scale = nodes.new("ShaderNodeCombineXYZ")
    links.new(roof_w.outputs[0], roof_scale.inputs["X"])
    links.new(roof_d.outputs[0], roof_scale.inputs["Y"])
    links.new(inp.outputs["Roof Height"], roof_scale.inputs["Z"])
    links.new(roof_scale.outputs["Vector"], roof_xform.inputs["Scale"])

    roof_z = nodes.new("ShaderNodeMath")
    roof_z.operation = "ADD"
    links.new(body_h.outputs[0], roof_z.inputs[0])
    roof_z2 = nodes.new("ShaderNodeMath")
    roof_z2.operation = "MULTIPLY"
    links.new(inp.outputs["Roof Height"], roof_z2.inputs[0])
    roof_z2.inputs[1].default_value = 0.5
    links.new(roof_z2.outputs[0], roof_z.inputs[1])
    links.new(roof_z.outputs[0], roof_pos.inputs["Z"])
    links.new(roof_pos.outputs["Vector"], roof_xform.inputs["Translation"])

    links.new(roof.outputs["Mesh"], roof_xform.inputs["Geometry"])

    # Gable: collapse top vertices to ridge (Y=0)
    bbox = nodes.new("GeometryNodeBoundBox")
    links.new(roof_xform.outputs["Geometry"], bbox.inputs["Geometry"])
    pos = nodes.new("GeometryNodeInputPosition")
    sep = nodes.new("ShaderNodeSeparateXYZ")
    links.new(pos.outputs["Position"], sep.inputs["Vector"])
    max_z = nodes.new("ShaderNodeSeparateXYZ")
    links.new(bbox.outputs["Max"], max_z.inputs["Vector"])
    cmp = nodes.new("ShaderNodeMath")
    cmp.operation = "GREATER_THAN"
    links.new(sep.outputs["Z"], cmp.inputs[0])
    # maxZ - epsilon
    max_minus = nodes.new("ShaderNodeMath")
    max_minus.operation = "SUBTRACT"
    links.new(max_z.outputs["Z"], max_minus.inputs[0])
    max_minus.inputs[1].default_value = 0.001
    links.new(max_minus.outputs[0], cmp.inputs[1])

    set_pos = nodes.new("GeometryNodeSetPosition")
    links.new(roof_xform.outputs["Geometry"], set_pos.inputs["Geometry"])
    links.new(cmp.outputs[0], set_pos.inputs["Selection"])
    comb = nodes.new("ShaderNodeCombineXYZ")
    links.new(sep.outputs["X"], comb.inputs["X"])
    comb.inputs["Y"].default_value = 0.0
    links.new(sep.outputs["Z"], comb.inputs["Z"])
    links.new(comb.outputs["Vector"], set_pos.inputs["Position"])
    links.new(set_pos.outputs["Geometry"], roof_mat.inputs["Geometry"])

    # Front windows
    win = nodes.new("GeometryNodeMeshCube")
    win_xform_l = nodes.new("GeometryNodeTransform")
    win_xform_r = nodes.new("GeometryNodeTransform")
    win_mat = nodes.new("GeometryNodeSetMaterial")

    win_w = nodes.new("ShaderNodeMath")
    win_w.operation = "MULTIPLY"
    links.new(inp.outputs["Width"], win_w.inputs[0])
    win_w.inputs[1].default_value = 0.18

    win_h = nodes.new("ShaderNodeMath")
    win_h.operation = "MULTIPLY"
    links.new(inp.outputs["Floor Height"], win_h.inputs[0])
    win_h.inputs[1].default_value = 0.6

    win_scale = nodes.new("ShaderNodeCombineXYZ")
    links.new(win_w.outputs[0], win_scale.inputs["X"])
    links.new(inp.outputs["Window Depth"], win_scale.inputs["Y"])
    links.new(win_h.outputs[0], win_scale.inputs["Z"])
    links.new(win_scale.outputs["Vector"], win_xform_l.inputs["Scale"])
    links.new(win_scale.outputs["Vector"], win_xform_r.inputs["Scale"])

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
    links.new(inp.outputs["Floor Height"], win_z.inputs[0])
    win_z.inputs[1].default_value = 0.65

    x_offset = nodes.new("ShaderNodeMath")
    x_offset.operation = "MULTIPLY"
    links.new(inp.outputs["Width"], x_offset.inputs[0])
    x_offset.inputs[1].default_value = 0.25

    win_pos_l = nodes.new("ShaderNodeCombineXYZ")
    links.new(x_offset.outputs[0], win_pos_l.inputs["X"])
    links.new(front_y2.outputs[0], win_pos_l.inputs["Y"])
    links.new(win_z.outputs[0], win_pos_l.inputs["Z"])
    win_pos_r = nodes.new("ShaderNodeCombineXYZ")
    x_neg = nodes.new("ShaderNodeMath")
    x_neg.operation = "MULTIPLY"
    links.new(x_offset.outputs[0], x_neg.inputs[0])
    x_neg.inputs[1].default_value = -1.0
    links.new(x_neg.outputs[0], win_pos_r.inputs["X"])
    links.new(front_y2.outputs[0], win_pos_r.inputs["Y"])
    links.new(win_z.outputs[0], win_pos_r.inputs["Z"])

    links.new(win.outputs["Mesh"], win_xform_l.inputs["Geometry"])
    links.new(win.outputs["Mesh"], win_xform_r.inputs["Geometry"])
    links.new(win_pos_l.outputs["Vector"], win_xform_l.inputs["Translation"])
    links.new(win_pos_r.outputs["Vector"], win_xform_r.inputs["Translation"])

    join_wins = nodes.new("GeometryNodeJoinGeometry")
    links.new(win_xform_l.outputs["Geometry"], join_wins.inputs["Geometry"])
    links.new(win_xform_r.outputs["Geometry"], join_wins.inputs["Geometry"])
    links.new(join_wins.outputs["Geometry"], win_mat.inputs["Geometry"])

    # Second-floor windows (only when floors >= 2)
    floors_ge2 = nodes.new("ShaderNodeMath")
    floors_ge2.operation = "GREATER_THAN"
    links.new(inp.outputs["Floors"], floors_ge2.inputs[0])
    floors_ge2.inputs[1].default_value = 1.5

    win2_xform_l = nodes.new("GeometryNodeTransform")
    win2_xform_r = nodes.new("GeometryNodeTransform")
    win2_mat = nodes.new("GeometryNodeSetMaterial")

    links.new(win_scale.outputs["Vector"], win2_xform_l.inputs["Scale"])
    links.new(win_scale.outputs["Vector"], win2_xform_r.inputs["Scale"])

    win2_z = nodes.new("ShaderNodeMath")
    win2_z.operation = "MULTIPLY"
    links.new(inp.outputs["Floor Height"], win2_z.inputs[0])
    win2_z.inputs[1].default_value = 1.65

    win2_pos_l = nodes.new("ShaderNodeCombineXYZ")
    links.new(x_offset.outputs[0], win2_pos_l.inputs["X"])
    links.new(front_y2.outputs[0], win2_pos_l.inputs["Y"])
    links.new(win2_z.outputs[0], win2_pos_l.inputs["Z"])
    win2_pos_r = nodes.new("ShaderNodeCombineXYZ")
    links.new(x_neg.outputs[0], win2_pos_r.inputs["X"])
    links.new(front_y2.outputs[0], win2_pos_r.inputs["Y"])
    links.new(win2_z.outputs[0], win2_pos_r.inputs["Z"])

    links.new(win.outputs["Mesh"], win2_xform_l.inputs["Geometry"])
    links.new(win.outputs["Mesh"], win2_xform_r.inputs["Geometry"])
    links.new(win2_pos_l.outputs["Vector"], win2_xform_l.inputs["Translation"])
    links.new(win2_pos_r.outputs["Vector"], win2_xform_r.inputs["Translation"])

    join_wins2 = nodes.new("GeometryNodeJoinGeometry")
    links.new(win2_xform_l.outputs["Geometry"], join_wins2.inputs["Geometry"])
    links.new(win2_xform_r.outputs["Geometry"], join_wins2.inputs["Geometry"])
    links.new(join_wins2.outputs["Geometry"], win2_mat.inputs["Geometry"])

    inv_ge2 = nodes.new("ShaderNodeMath")
    inv_ge2.operation = "SUBTRACT"
    inv_ge2.inputs[0].default_value = 1.0
    links.new(floors_ge2.outputs[0], inv_ge2.inputs[1])

    del_win2 = nodes.new("GeometryNodeDeleteGeometry")
    links.new(win2_mat.outputs["Geometry"], del_win2.inputs["Geometry"])
    links.new(inv_ge2.outputs[0], del_win2.inputs["Selection"])

    # Door
    door = nodes.new("GeometryNodeMeshCube")
    door_xform = nodes.new("GeometryNodeTransform")
    door_mat = nodes.new("GeometryNodeSetMaterial")

    door_scale = nodes.new("ShaderNodeCombineXYZ")
    door_scale.inputs["X"].default_value = 1.2
    door_scale.inputs["Y"].default_value = 0.06
    door_scale.inputs["Z"].default_value = 2.2
    links.new(door_scale.outputs["Vector"], door_xform.inputs["Scale"])

    door_y = nodes.new("ShaderNodeMath")
    door_y.operation = "ADD"
    door_depth_half = nodes.new("ShaderNodeMath")
    door_depth_half.operation = "MULTIPLY"
    door_depth_half.inputs[0].default_value = 0.06
    door_depth_half.inputs[1].default_value = 0.5
    links.new(depth_half.outputs[0], door_y.inputs[0])
    links.new(door_depth_half.outputs[0], door_y.inputs[1])
    door_y2 = nodes.new("ShaderNodeMath")
    door_y2.operation = "SUBTRACT"
    links.new(door_y.outputs[0], door_y2.inputs[0])
    door_y2.inputs[1].default_value = 0.01

    door_pos = nodes.new("ShaderNodeCombineXYZ")
    links.new(door_y2.outputs[0], door_pos.inputs["Y"])
    door_pos.inputs["Z"].default_value = 1.1
    links.new(door_pos.outputs["Vector"], door_xform.inputs["Translation"])

    links.new(door.outputs["Mesh"], door_xform.inputs["Geometry"])
    links.new(door_xform.outputs["Geometry"], door_mat.inputs["Geometry"])

    # Side windows
    side = nodes.new("GeometryNodeMeshCube")
    side_xform_l = nodes.new("GeometryNodeTransform")
    side_xform_r = nodes.new("GeometryNodeTransform")
    side_mat = nodes.new("GeometryNodeSetMaterial")

    side_scale = nodes.new("ShaderNodeCombineXYZ")
    side_scale.inputs["X"].default_value = 0.04
    side_scale.inputs["Y"].default_value = 1.0
    side_scale.inputs["Z"].default_value = 0.7
    links.new(side_scale.outputs["Vector"], side_xform_l.inputs["Scale"])
    links.new(side_scale.outputs["Vector"], side_xform_r.inputs["Scale"])

    side_x = nodes.new("ShaderNodeMath")
    side_x.operation = "MULTIPLY"
    side_depth_half = nodes.new("ShaderNodeMath")
    side_depth_half.operation = "MULTIPLY"
    side_depth_half.inputs[0].default_value = 0.04
    side_depth_half.inputs[1].default_value = 0.5
    links.new(inp.outputs["Width"], side_x.inputs[0])
    side_x.inputs[1].default_value = 0.5
    side_x2 = nodes.new("ShaderNodeMath")
    side_x2.operation = "ADD"
    links.new(side_x.outputs[0], side_x2.inputs[0])
    links.new(side_depth_half.outputs[0], side_x2.inputs[1])
    side_x3 = nodes.new("ShaderNodeMath")
    side_x3.operation = "SUBTRACT"
    links.new(side_x2.outputs[0], side_x3.inputs[0])
    side_x3.inputs[1].default_value = 0.01

    side_pos_l = nodes.new("ShaderNodeCombineXYZ")
    links.new(side_x3.outputs[0], side_pos_l.inputs["X"])
    side_pos_l.inputs["Y"].default_value = -1.2
    side_pos_l.inputs["Z"].default_value = 2.1

    side_pos_r = nodes.new("ShaderNodeCombineXYZ")
    side_x_neg = nodes.new("ShaderNodeMath")
    side_x_neg.operation = "MULTIPLY"
    links.new(side_x3.outputs[0], side_x_neg.inputs[0])
    side_x_neg.inputs[1].default_value = -1.0
    links.new(side_x_neg.outputs[0], side_pos_r.inputs["X"])
    side_pos_r.inputs["Y"].default_value = -1.2
    side_pos_r.inputs["Z"].default_value = 2.1

    links.new(side.outputs["Mesh"], side_xform_l.inputs["Geometry"])
    links.new(side.outputs["Mesh"], side_xform_r.inputs["Geometry"])
    links.new(side_pos_l.outputs["Vector"], side_xform_l.inputs["Translation"])
    links.new(side_pos_r.outputs["Vector"], side_xform_r.inputs["Translation"])

    join_side = nodes.new("GeometryNodeJoinGeometry")
    links.new(side_xform_l.outputs["Geometry"], join_side.inputs["Geometry"])
    links.new(side_xform_r.outputs["Geometry"], join_side.inputs["Geometry"])
    links.new(join_side.outputs["Geometry"], side_mat.inputs["Geometry"])

    # Join all parts
    join_all = nodes.new("GeometryNodeJoinGeometry")
    links.new(body_mat.outputs["Geometry"], join_all.inputs["Geometry"])
    links.new(roof_mat.outputs["Geometry"], join_all.inputs["Geometry"])
    links.new(win_mat.outputs["Geometry"], join_all.inputs["Geometry"])
    links.new(del_win2.outputs["Geometry"], join_all.inputs["Geometry"])
    links.new(door_mat.outputs["Geometry"], join_all.inputs["Geometry"])
    links.new(side_mat.outputs["Geometry"], join_all.inputs["Geometry"])
    links.new(join_all.outputs["Geometry"], out.inputs["Geometry"])

    return ng, body_mat, roof_mat, win_mat, win2_mat, door_mat, side_mat


def main():
    args = parse_args({
        "floors": 1,
        "out": "",
        "width": 8.0,
        "depth": 6.0,
        "floor_height": 3.0,
        "roof_height": 2.0,
        "window_depth": 0.04,
    })

    set_scene_defaults()

    mesh = bpy.data.meshes.new("house_mesh")
    mesh.from_pydata([(0, 0, 0)], [], [])
    obj = bpy.data.objects.new("house", mesh)
    bpy.context.collection.objects.link(obj)

    mat_body = get_palette_material("matte_cream")
    mat_roof = get_palette_material("matte_sakura")
    mat_windows = get_palette_material("matte_sky")
    mat_door = get_palette_material("matte_charcoal")

    ng, body_mat, roof_mat, win_mat, win2_mat, door_mat, side_mat = build_house_group(args)
    body_mat.inputs["Material"].default_value = mat_body
    roof_mat.inputs["Material"].default_value = mat_roof
    win_mat.inputs["Material"].default_value = mat_windows
    win2_mat.inputs["Material"].default_value = mat_windows
    door_mat.inputs["Material"].default_value = mat_door
    side_mat.inputs["Material"].default_value = mat_windows

    mod = obj.modifiers.new(name="GN_House", type="NODES")
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
