import bpy
from common import set_scene_defaults, get_palette_material, parse_args, add_group_input, add_group_output


def build_fence_group(args):
    ng = bpy.data.node_groups.new("GN_Fence", 'GeometryNodeTree')
    add_group_input(ng, "Length", "NodeSocketFloat", args.length)
    add_group_input(ng, "Post Spacing", "NodeSocketFloat", args.post_spacing)
    add_group_input(ng, "Post Height", "NodeSocketFloat", args.post_height)
    add_group_input(ng, "Post Width", "NodeSocketFloat", args.post_width)
    add_group_input(ng, "Rail Height", "NodeSocketFloat", args.rail_height)
    add_group_input(ng, "Rail Thickness", "NodeSocketFloat", args.rail_thickness)
    add_group_output(ng, "Geometry", "NodeSocketGeometry")

    nodes = ng.nodes
    links = ng.links

    input_node = nodes.new("NodeGroupInput")
    output_node = nodes.new("NodeGroupOutput")

    mesh_line = nodes.new("GeometryNodeMeshLine")
    mesh_line.mode = 'OFFSET'
    mesh_line.inputs["Count"].default_value = max(2, int(args.length / args.post_spacing) + 1)
    mesh_line.inputs["Offset"].default_value = (args.post_spacing, 0.0, 0.0)

    post = nodes.new("GeometryNodeMeshCube")
    post.inputs["Size"].default_value = (args.post_width, args.post_width, args.post_height)

    post_xform = nodes.new("GeometryNodeTransform")
    post_xform.inputs["Translation"].default_value = (0.0, 0.0, args.post_height * 0.5)

    mesh_to_points = nodes.new("GeometryNodeMeshToPoints")
    instance_posts = nodes.new("GeometryNodeInstanceOnPoints")
    realize = nodes.new("GeometryNodeRealizeInstances")
    post_mat = nodes.new("GeometryNodeSetMaterial")

    rail = nodes.new("GeometryNodeMeshCube")
    rail.inputs["Size"].default_value = (args.length, args.rail_thickness, args.rail_thickness)

    rail_xform = nodes.new("GeometryNodeTransform")
    rail_xform.inputs["Translation"].default_value = (args.length * 0.5, 0.0, args.rail_height)

    rail2_xform = nodes.new("GeometryNodeTransform")
    rail2_xform.inputs["Translation"].default_value = (args.length * 0.5, 0.0, args.rail_height * 0.5)

    join_rails = nodes.new("GeometryNodeJoinGeometry")
    rail_mat = nodes.new("GeometryNodeSetMaterial")

    join = nodes.new("GeometryNodeJoinGeometry")

    # Posts
    links.new(mesh_line.outputs["Mesh"], mesh_to_points.inputs["Mesh"])
    links.new(mesh_to_points.outputs["Points"], instance_posts.inputs["Points"])
    links.new(post.outputs["Mesh"], post_xform.inputs["Geometry"])
    links.new(post_xform.outputs["Geometry"], instance_posts.inputs["Instance"])
    links.new(instance_posts.outputs["Instances"], realize.inputs["Geometry"])
    links.new(realize.outputs["Geometry"], post_mat.inputs["Geometry"])

    # Rails
    links.new(rail.outputs["Mesh"], rail_xform.inputs["Geometry"])
    links.new(rail.outputs["Mesh"], rail2_xform.inputs["Geometry"])

    links.new(rail_xform.outputs["Geometry"], join_rails.inputs["Geometry"])
    links.new(rail2_xform.outputs["Geometry"], join_rails.inputs["Geometry"])
    links.new(join_rails.outputs["Geometry"], rail_mat.inputs["Geometry"])

    # Join
    links.new(post_mat.outputs["Geometry"], join.inputs["Geometry"])
    links.new(rail_mat.outputs["Geometry"], join.inputs["Geometry"])
    links.new(join.outputs["Geometry"], output_node.inputs["Geometry"])

    return ng, post_mat, rail_mat


def main():
    args = parse_args({
        "length": 2.0,
        "post_spacing": 0.5,
        "post_height": 1.1,
        "post_width": 0.08,
        "rail_height": 0.8,
        "rail_thickness": 0.06,
    })

    set_scene_defaults()

    mesh = bpy.data.meshes.new("fence_mesh")
    mesh.from_pydata([(0, 0, 0)], [], [])
    obj = bpy.data.objects.new("fence", mesh)
    bpy.context.collection.objects.link(obj)

    mat_posts = get_palette_material("matte_asphalt")
    mat_rails = get_palette_material("matte_charcoal")

    ng, post_mat, rail_mat = build_fence_group(args)
    post_mat.inputs["Material"].default_value = mat_posts
    rail_mat.inputs["Material"].default_value = mat_rails

    mod = obj.modifiers.new(name="GN_Fence", type='NODES')
    mod.node_group = ng


if __name__ == "__main__":
    main()
