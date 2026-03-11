# Export Checklist (GLB + Three.js)

## Before Export
- Apply transforms (scale = 1, rotation = 0).
- Set pivot to target placement point.
- Remove hidden interior geometry.
- Ensure materials are PBR-compatible.

## Export Settings (Blender glTF 2.0)
- Format: GLB
- Include: Meshes, Materials
- Apply modifiers: Yes
- Compression: Optional (Draco later)

## Validate in Three.js
1. Place on 1m grid.
2. Confirm scale consistency.
3. Check pivot alignment.
4. Verify roughness/metalness response.
