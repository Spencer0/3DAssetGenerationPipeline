# Prefab Chunks (10x10)

## Units + Footprints
- Blender units: meters.
- Three.js units: 1 unit = 1 meter.
- Footprint source of truth: runtime `Box3` in Three.js (width = X, depth = Z).

## Chunk Definition
- Fixed grid: 50x50 cells.
- Cell size: 1 meter.
- Chunk footprint: 50m x 50m, centered at origin for editing.

## Chunk JSON (editor state)
```json
{
  "tiles": [["road_center", "..."], ["..."]],
  "objects": [
    { "asset": "house_1f.glb", "pos": [x, y, z], "rotY": 0, "scale": 1 }
  ]
}
```

## GLB Export
- Use `GLTFExporter` to export a single Three.js Group containing tiles + objects.
- GLB is the shareable artifact across repos/projects.
- Hitboxes/colliders are computed at runtime by the consumer game using bounding boxes.
