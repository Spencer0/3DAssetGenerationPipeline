import math
import bpy
from common import set_scene_defaults, get_palette_material, parse_args, add_group_input, add_group_output


def build_apartment_group(args):
    ng = bpy.data.node_groups.new("GN_Apartment", 'GeometryNodeTree')
    add_group_input(ng, "Width", "NodeSocketFloat", args.width)
    add_group_input(ng, "Depth", "NodeSocketFloat", args.depth)
    add_group_input(ng, "Height", "NodeSocketFloat", args.height)
    add_group_input(ng, "Window Cols", "NodeSocketInt", args.window_cols)
    add_group_input(ng, "Window Rows", "NodeSocketInt", args.window_rows)
    add_group_input(ng, "Window Depth", "NodeSocketFloat", args.window_depth)
    add_group_output(ng, "Geometry", "NodeSocketGeometry")

    nodes = ng.nodes
    links = ng.links

    input_node = nodes.new("NodeGroupInput")
    output_node = nodes.new("NodeGroupOutput")

    building = nodes.new("GeometryNodeMeshCube")
    building_xform = nodes.new("GeometryNodeTransform")
    building_mat = nodes.new("GeometryNodeSetMaterial")

    grid_front_left = nodes.new("GeometryNodeMeshGrid")
    grid_front_right = nodes.new("GeometryNodeMeshGrid")
    grid_back = nodes.new("GeometryNodeMeshGrid")
    grid_side = nodes.new("GeometryNodeMeshGrid")

    front_left_xform = nodes.new("GeometryNodeTransform")
    front_right_xform = nodes.new("GeometryNodeTransform")
    back_xform = nodes.new("GeometryNodeTransform")
    left_xform = nodes.new("GeometryNodeTransform")
    right_xform = nodes.new("GeometryNodeTransform")

    front_left_points = nodes.new("GeometryNodeMeshToPoints")
    front_right_points = nodes.new("GeometryNodeMeshToPoints")
    back_points = nodes.new("GeometryNodeMeshToPoints")
    left_points = nodes.new("GeometryNodeMeshToPoints")
    right_points = nodes.new("GeometryNodeMeshToPoints")

    front_left_instance = nodes.new("GeometryNodeInstanceOnPoints")
    front_right_instance = nodes.new("GeometryNodeInstanceOnPoints")
    back_instance = nodes.new("GeometryNodeInstanceOnPoints")
    left_instance = nodes.new("GeometryNodeInstanceOnPoints")
    right_instance = nodes.new("GeometryNodeInstanceOnPoints")

    front_left_realize = nodes.new("GeometryNodeRealizeInstances")
    front_right_realize = nodes.new("GeometryNodeRealizeInstances")
    back_realize = nodes.new("GeometryNodeRealizeInstances")
    left_realize = nodes.new("GeometryNodeRealizeInstances")
    right_realize = nodes.new("GeometryNodeRealizeInstances")

    window_front = nodes.new("GeometryNodeMeshCube")
    window_side = nodes.new("GeometryNodeMeshCube")
    window_mat = nodes.new("GeometryNodeSetMaterial")

    join_windows = nodes.new("GeometryNodeJoinGeometry")
    join_all = nodes.new("GeometryNodeJoinGeometry")

    door = nodes.new("GeometryNodeMeshCube")
    door_xform = nodes.new("GeometryNodeTransform")
    door_mat = nodes.new("GeometryNodeSetMaterial")

    ac = nodes.new("GeometryNodeMeshCube")
    ac_xform = nodes.new("GeometryNodeTransform")
    ac_mat = nodes.new("GeometryNodeSetMaterial")

    # Building
    building.inputs["Size"].default_value = (args.width, args.depth, args.height)
    links.new(building.outputs["Mesh"], building_xform.inputs["Geometry"])
    building_xform.inputs["Translation"].default_value = (0.0, 0.0, args.height * 0.5)
    links.new(building_xform.outputs["Geometry"], building_mat.inputs["Geometry"])

    # Window grids (front split to avoid door zone)
    grid_front_left.inputs["Size X"].default_value = args.width * 0.35
    grid_front_left.inputs["Size Y"].default_value = args.height * 0.65
    grid_front_left.inputs["Vertices X"].default_value = max(2, args.window_cols)
    grid_front_left.inputs["Vertices Y"].default_value = max(2, args.window_rows - 1)

    grid_front_right.inputs["Size X"].default_value = args.width * 0.35
    grid_front_right.inputs["Size Y"].default_value = args.height * 0.65
    grid_front_right.inputs["Vertices X"].default_value = max(2, args.window_cols)
    grid_front_right.inputs["Vertices Y"].default_value = max(2, args.window_rows - 1)

    grid_back.inputs["Size X"].default_value = args.width * 0.8
    grid_back.inputs["Size Y"].default_value = args.height * 0.8
    grid_back.inputs["Vertices X"].default_value = max(2, args.window_cols)
    grid_back.inputs["Vertices Y"].default_value = max(2, args.window_rows)

    grid_side.inputs["Size X"].default_value = args.depth * 0.8
    grid_side.inputs["Size Y"].default_value = args.height * 0.8
    grid_side.inputs["Vertices X"].default_value = max(2, args.window_cols)
    grid_side.inputs["Vertices Y"].default_value = max(2, args.window_rows)

    # Front/back faces (XZ plane)
    front_left_xform.inputs["Rotation"].default_value = (math.radians(90.0), 0.0, 0.0)
    front_right_xform.inputs["Rotation"].default_value = (math.radians(90.0), 0.0, 0.0)
    back_xform.inputs["Rotation"].default_value = (math.radians(90.0), 0.0, 0.0)
    front_left_xform.inputs["Translation"].default_value = (-args.width * 0.22, args.depth * 0.5 + args.window_depth * 0.5 - 0.01, args.height * 0.6)
    front_right_xform.inputs["Translation"].default_value = (args.width * 0.22, args.depth * 0.5 + args.window_depth * 0.5 - 0.01, args.height * 0.6)
    back_xform.inputs["Translation"].default_value = (0.0, -args.depth * 0.5 - args.window_depth * 0.5 + 0.01, args.height * 0.5)

    links.new(grid_front_left.outputs["Mesh"], front_left_xform.inputs["Geometry"])
    links.new(grid_front_right.outputs["Mesh"], front_right_xform.inputs["Geometry"])
    links.new(grid_back.outputs["Mesh"], back_xform.inputs["Geometry"])

    # Left/right faces (YZ plane)
    left_xform.inputs["Rotation"].default_value = (math.radians(90.0), 0.0, math.radians(90.0))
    right_xform.inputs["Rotation"].default_value = (math.radians(90.0), 0.0, math.radians(90.0))
    left_xform.inputs["Translation"].default_value = (-args.width * 0.5 - args.window_depth * 0.5 + 0.01, 0.0, args.height * 0.5)
    right_xform.inputs["Translation"].default_value = (args.width * 0.5 + args.window_depth * 0.5 - 0.01, 0.0, args.height * 0.5)

    links.new(grid_side.outputs["Mesh"], left_xform.inputs["Geometry"])
    links.new(grid_side.outputs["Mesh"], right_xform.inputs["Geometry"])

    # Window geometry
    window_w = max(0.2, (args.width * 0.7) / max(2, args.window_cols))
    window_h = max(0.3, (args.height * 0.7) / max(2, args.window_rows))
    window_front.inputs["Size"].default_value = (window_w, args.window_depth, window_h)
    window_side.inputs["Size"].default_value = (args.window_depth, window_w, window_h)

    # Convert to points and instance
    links.new(front_left_xform.outputs["Geometry"], front_left_points.inputs["Mesh"])
    links.new(front_right_xform.outputs["Geometry"], front_right_points.inputs["Mesh"])
    links.new(back_xform.outputs["Geometry"], back_points.inputs["Mesh"])
    links.new(left_xform.outputs["Geometry"], left_points.inputs["Mesh"])
    links.new(right_xform.outputs["Geometry"], right_points.inputs["Mesh"])

    links.new(front_left_points.outputs["Points"], front_left_instance.inputs["Points"])
    links.new(front_right_points.outputs["Points"], front_right_instance.inputs["Points"])
    links.new(back_points.outputs["Points"], back_instance.inputs["Points"])
    links.new(left_points.outputs["Points"], left_instance.inputs["Points"])
    links.new(right_points.outputs["Points"], right_instance.inputs["Points"])

    links.new(window_front.outputs["Mesh"], front_left_instance.inputs["Instance"])
    links.new(window_front.outputs["Mesh"], front_right_instance.inputs["Instance"])
    links.new(window_front.outputs["Mesh"], back_instance.inputs["Instance"])
    links.new(window_side.outputs["Mesh"], left_instance.inputs["Instance"])
    links.new(window_side.outputs["Mesh"], right_instance.inputs["Instance"])

    links.new(front_left_instance.outputs["Instances"], front_left_realize.inputs["Geometry"])
    links.new(front_right_instance.outputs["Instances"], front_right_realize.inputs["Geometry"])
    links.new(back_instance.outputs["Instances"], back_realize.inputs["Geometry"])
    links.new(left_instance.outputs["Instances"], left_realize.inputs["Geometry"])
    links.new(right_instance.outputs["Instances"], right_realize.inputs["Geometry"])

    links.new(front_left_realize.outputs["Geometry"], join_windows.inputs["Geometry"])
    links.new(front_right_realize.outputs["Geometry"], join_windows.inputs["Geometry"])
    links.new(back_realize.outputs["Geometry"], join_windows.inputs["Geometry"])
    links.new(left_realize.outputs["Geometry"], join_windows.inputs["Geometry"])
    links.new(right_realize.outputs["Geometry"], join_windows.inputs["Geometry"])

    links.new(join_windows.outputs["Geometry"], window_mat.inputs["Geometry"])

    # Door (front face)
    door.inputs["Size"].default_value = (1.2, args.window_depth, 2.2)
    door_xform.inputs["Translation"].default_value = (0.0, args.depth * 0.5 + args.window_depth * 0.5 - 0.01, 1.1)
    links.new(door.outputs["Mesh"], door_xform.inputs["Geometry"])
    links.new(door_xform.outputs["Geometry"], door_mat.inputs["Geometry"])

    # AC unit (roof)
    ac.inputs["Size"].default_value = (1.6, 1.0, 0.6)
    ac_xform.inputs["Translation"].default_value = (args.width * 0.2, args.depth * -0.2, args.height + 0.3)
    links.new(ac.outputs["Mesh"], ac_xform.inputs["Geometry"])
    links.new(ac_xform.outputs["Geometry"], ac_mat.inputs["Geometry"])

    # Join
    links.new(building_mat.outputs["Geometry"], join_all.inputs["Geometry"])
    links.new(window_mat.outputs["Geometry"], join_all.inputs["Geometry"])
    links.new(door_mat.outputs["Geometry"], join_all.inputs["Geometry"])
    links.new(ac_mat.outputs["Geometry"], join_all.inputs["Geometry"])
    links.new(join_all.outputs["Geometry"], output_node.inputs["Geometry"])

    return ng, building_mat, window_mat, door_mat, ac_mat


def main():
    args = parse_args({
        "width": 8.0,
        "depth": 12.0,
        "height": 12.0,
        "window_cols": 4,
        "window_rows": 6,
        "window_depth": 0.04,
    })

    set_scene_defaults()

    mesh = bpy.data.meshes.new("apartment_mesh")
    mesh.from_pydata([(0, 0, 0)], [], [])
    obj = bpy.data.objects.new("apartment", mesh)
    bpy.context.collection.objects.link(obj)

    mat_building = get_palette_material("matte_cream")
    mat_windows = get_palette_material("matte_sky")
    mat_door = get_palette_material("matte_charcoal")
    mat_ac = get_palette_material("matte_asphalt")

    ng, building_mat, window_mat, door_mat, ac_mat = build_apartment_group(args)
    building_mat.inputs["Material"].default_value = mat_building
    window_mat.inputs["Material"].default_value = mat_windows
    door_mat.inputs["Material"].default_value = mat_door
    ac_mat.inputs["Material"].default_value = mat_ac

    mod = obj.modifiers.new(name="GN_Apartment", type='NODES')
    mod.node_group = ng


if __name__ == "__main__":
    main()
