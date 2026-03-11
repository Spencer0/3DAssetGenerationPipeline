import bpy
from common import set_scene_defaults, get_palette_material, parse_args, add_group_input, add_group_output


def build_tree_group(args):
    ng = bpy.data.node_groups.new("GN_Tree", 'GeometryNodeTree')
    add_group_input(ng, "Trunk Height", "NodeSocketFloat", args.trunk_height)
    add_group_input(ng, "Trunk Radius", "NodeSocketFloat", args.trunk_radius)
    add_group_input(ng, "Canopy Radius", "NodeSocketFloat", args.canopy_radius)
    add_group_input(ng, "Blossom Density", "NodeSocketFloat", args.blossom_density)
    add_group_input(ng, "Blossom Radius", "NodeSocketFloat", args.blossom_radius)
    add_group_input(ng, "Extra Canopy Scale", "NodeSocketFloat", args.extra_canopy_scale)
    add_group_input(ng, "Extra Canopy Offset", "NodeSocketFloat", args.extra_canopy_offset)
    add_group_output(ng, "Geometry", "NodeSocketGeometry")

    nodes = ng.nodes
    links = ng.links

    input_node = nodes.new("NodeGroupInput")
    output_node = nodes.new("NodeGroupOutput")

    trunk = nodes.new("GeometryNodeMeshCylinder")
    trunk.inputs["Vertices"].default_value = 16

    trunk_xform = nodes.new("GeometryNodeTransform")

    trunk_mat = nodes.new("GeometryNodeSetMaterial")

    canopy = nodes.new("GeometryNodeMeshIcoSphere")
    canopy.inputs["Subdivisions"].default_value = 2

    canopy_xform = nodes.new("GeometryNodeTransform")
    canopy_join = nodes.new("GeometryNodeJoinGeometry")
    canopy_mat = nodes.new("GeometryNodeSetMaterial")

    canopy2 = nodes.new("GeometryNodeMeshIcoSphere")
    canopy2.inputs["Subdivisions"].default_value = 2
    canopy2_xform = nodes.new("GeometryNodeTransform")

    canopy3 = nodes.new("GeometryNodeMeshIcoSphere")
    canopy3.inputs["Subdivisions"].default_value = 2
    canopy3_xform = nodes.new("GeometryNodeTransform")

    canopy4 = nodes.new("GeometryNodeMeshIcoSphere")
    canopy4.inputs["Subdivisions"].default_value = 2
    canopy4_xform = nodes.new("GeometryNodeTransform")

    distribute = nodes.new("GeometryNodeDistributePointsOnFaces")
    distribute.inputs["Density"].default_value = args.blossom_density

    blossom = nodes.new("GeometryNodeMeshIcoSphere")
    blossom.inputs["Subdivisions"].default_value = 1

    instance = nodes.new("GeometryNodeInstanceOnPoints")
    scale_instances = nodes.new("GeometryNodeScaleInstances")

    blossom_mat = nodes.new("GeometryNodeSetMaterial")

    join = nodes.new("GeometryNodeJoinGeometry")

    # Trunk
    links.new(input_node.outputs["Trunk Radius"], trunk.inputs["Radius"])
    links.new(input_node.outputs["Trunk Height"], trunk.inputs["Depth"])
    links.new(trunk.outputs["Mesh"], trunk_xform.inputs["Geometry"])
    trunk_xform.inputs["Translation"].default_value = (0.0, 0.0, args.trunk_height * 0.5)
    links.new(trunk_xform.outputs["Geometry"], trunk_mat.inputs["Geometry"])

    # Canopy
    links.new(input_node.outputs["Canopy Radius"], canopy.inputs["Radius"])
    links.new(canopy.outputs["Mesh"], canopy_xform.inputs["Geometry"])
    canopy_xform.inputs["Translation"].default_value = (0.0, 0.0, args.trunk_height + args.canopy_radius * 0.6)

    # Extra canopy heads for large variant
    links.new(input_node.outputs["Canopy Radius"], canopy2.inputs["Radius"])
    links.new(input_node.outputs["Canopy Radius"], canopy3.inputs["Radius"])
    links.new(input_node.outputs["Canopy Radius"], canopy4.inputs["Radius"])

    canopy2_xform.inputs["Translation"].default_value = (args.extra_canopy_offset, 0.0, args.trunk_height + args.canopy_radius * 0.4)
    canopy3_xform.inputs["Translation"].default_value = (-args.extra_canopy_offset, 0.0, args.trunk_height + args.canopy_radius * 0.4)
    canopy4_xform.inputs["Translation"].default_value = (0.0, args.extra_canopy_offset, args.trunk_height + args.canopy_radius * 0.5)

    canopy2_xform.inputs["Scale"].default_value = (args.extra_canopy_scale, args.extra_canopy_scale, args.extra_canopy_scale)
    canopy3_xform.inputs["Scale"].default_value = (args.extra_canopy_scale, args.extra_canopy_scale, args.extra_canopy_scale)
    canopy4_xform.inputs["Scale"].default_value = (args.extra_canopy_scale, args.extra_canopy_scale, args.extra_canopy_scale)

    links.new(canopy2.outputs["Mesh"], canopy2_xform.inputs["Geometry"])
    links.new(canopy3.outputs["Mesh"], canopy3_xform.inputs["Geometry"])
    links.new(canopy4.outputs["Mesh"], canopy4_xform.inputs["Geometry"])

    links.new(canopy_xform.outputs["Geometry"], canopy_join.inputs["Geometry"])
    links.new(canopy2_xform.outputs["Geometry"], canopy_join.inputs["Geometry"])
    links.new(canopy3_xform.outputs["Geometry"], canopy_join.inputs["Geometry"])
    links.new(canopy4_xform.outputs["Geometry"], canopy_join.inputs["Geometry"])
    links.new(canopy_join.outputs["Geometry"], canopy_mat.inputs["Geometry"])

    # Blossoms
    links.new(canopy.outputs["Mesh"], distribute.inputs["Mesh"])
    links.new(distribute.outputs["Points"], instance.inputs["Points"])
    links.new(blossom.outputs["Mesh"], instance.inputs["Instance"])
    links.new(input_node.outputs["Blossom Radius"], blossom.inputs["Radius"])
    links.new(instance.outputs["Instances"], scale_instances.inputs["Instances"])
    scale_instances.inputs["Scale"].default_value = (1.0, 1.0, 1.0)
    links.new(scale_instances.outputs["Instances"], blossom_mat.inputs["Geometry"])

    # Join
    links.new(trunk_mat.outputs["Geometry"], join.inputs["Geometry"])
    links.new(canopy_mat.outputs["Geometry"], join.inputs["Geometry"])
    links.new(blossom_mat.outputs["Geometry"], join.inputs["Geometry"])
    links.new(join.outputs["Geometry"], output_node.inputs["Geometry"])

    return ng, trunk_mat, canopy_mat, blossom_mat


def main():
    args = parse_args({
        "trunk_height": 2.2,
        "trunk_radius": 0.15,
        "canopy_radius": 1.4,
        "blossom_density": 40.0,
        "blossom_radius": 0.05,
        "extra_canopy_scale": 0.0,
        "extra_canopy_offset": 0.0,
    })

    set_scene_defaults()

    mesh = bpy.data.meshes.new("tree_mesh")
    mesh.from_pydata([(0, 0, 0)], [], [])
    obj = bpy.data.objects.new("tree", mesh)
    bpy.context.collection.objects.link(obj)

    mat_trunk = get_palette_material("matte_charcoal")
    mat_canopy = get_palette_material("matte_sakura")
    mat_blossom = get_palette_material("matte_cream")

    ng, trunk_mat, canopy_mat, blossom_mat = build_tree_group(args)
    trunk_mat.inputs["Material"].default_value = mat_trunk
    canopy_mat.inputs["Material"].default_value = mat_canopy
    blossom_mat.inputs["Material"].default_value = mat_blossom

    mod = obj.modifiers.new(name="GN_Tree", type='NODES')
    mod.node_group = ng


if __name__ == "__main__":
    main()
