import math
import bpy
from common import parse_args

ASSET_SPECS = {
    "fruit": (0.12, 0.12, 0.12),
    "tree": (3.2, 3.2, 3.5),
    "apartment": (8.0, 12.0, 12.0),
    "vending": (1.0, 0.5, 0.75),
    "car": (3.6, 1.6, 1.4),
    "fence": (2.0, 0.1, 1.1),
    "basketball": (0.24, 0.24, 0.24),
}


def get_bounds(obj):
    bbox = [obj.matrix_world @ bpy.mathutils.Vector(corner) for corner in obj.bound_box]
    xs = [v.x for v in bbox]
    ys = [v.y for v in bbox]
    zs = [v.z for v in bbox]
    return (min(xs), max(xs)), (min(ys), max(ys)), (min(zs), max(zs))


def main():
    args = parse_args({
        "asset_type": "",
        "tolerance": 0.2,
    })

    if not args.asset_type or args.asset_type not in ASSET_SPECS:
        print("Unknown or missing asset_type. Valid:", ", ".join(ASSET_SPECS.keys()))
        return

    meshes = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH']
    if not meshes:
        print("No mesh objects found.")
        return

    # Combine bounds across all mesh objects
    bounds = None
    for obj in meshes:
        x, y, z = get_bounds(obj)
        if bounds is None:
            bounds = [x, y, z]
        else:
            bounds[0] = (min(bounds[0][0], x[0]), max(bounds[0][1], x[1]))
            bounds[1] = (min(bounds[1][0], y[0]), max(bounds[1][1], y[1]))
            bounds[2] = (min(bounds[2][0], z[0]), max(bounds[2][1], z[1]))

    (xmin, xmax), (ymin, ymax), (zmin, zmax) = bounds
    size = (xmax - xmin, ymax - ymin, zmax - zmin)

    expected = ASSET_SPECS[args.asset_type]
    tol = args.tolerance

    for axis, actual, exp in zip(["X", "Y", "Z"], size, expected):
        if not (exp * (1 - tol) <= actual <= exp * (1 + tol)):
            print(f"WARN: {axis} size {actual:.2f}m outside {exp:.2f}m +/- {tol*100:.0f}%")

    # Pivot checks
    if abs(xmin + xmax) > 0.05:
        print("WARN: Pivot not centered on X axis.")
    if abs(ymin + ymax) > 0.05:
        print("WARN: Pivot not centered on Y axis.")
    if abs(zmin) > 0.02:
        print("WARN: Pivot not at bottom (Z min not near 0).")

    print("Validation complete.")


if __name__ == "__main__":
    main()
